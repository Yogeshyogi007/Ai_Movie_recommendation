from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Movie, Rating, User, db, Recommendation
from .movie_recommender import MovieRecommender
from .forms import GenreSelectionForm
from sqlalchemy import func, or_
import random

main = Blueprint('main', __name__)

def get_recommender():
    return MovieRecommender()

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    # Get user's rated movies
    user_ratings = db.session.query(Rating).join(
        Movie, Rating.movie_id == Movie.id
    ).filter(
        Rating.user_id == current_user.id
    ).order_by(Rating.timestamp.desc()).all()

    # Get saved recommendations
    saved_recommendations = db.session.query(Recommendation).join(
        Movie, Recommendation.movie_id == Movie.id
    ).filter(
        Recommendation.user_id == current_user.id
    ).order_by(Recommendation.score.desc()).all()
    
    # Debug logging
    print(f"User {current_user.id} has {len(user_ratings)} ratings")
    print(f"Found {len(saved_recommendations)} saved recommendations")
    if saved_recommendations:
        print("Saved recommendation titles:")
        for rec in saved_recommendations:
            print(f"- {rec.movie.title} (score: {rec.score})")

    return render_template(
        'profile.html',
        user_ratings=user_ratings,
        recommendations=[rec.movie for rec in saved_recommendations],
        debug_info={
            'num_ratings': len(user_ratings),
            'num_recommendations': len(saved_recommendations)
        }
    )

@main.route('/genre_selection', methods=['GET', 'POST'])
@login_required
def genre_selection():
    form = GenreSelectionForm()
    
    # Get unique genres from movies
    genres = db.session.query(Movie.genres).distinct().all()
    all_genres = set()
    for genre in genres:
        all_genres.update(genre[0].split('|'))
    
    # Set choices for the form
    form.genres.choices = [(g, g) for g in sorted(all_genres)]
    
    if form.validate_on_submit():
        selected_genres = form.genres.data
        current_user.preferred_genres = ','.join(selected_genres)
        db.session.commit()
        return redirect(url_for('main.movie_selection'))
    
    return render_template('genre_selection.html', form=form, genres=sorted(all_genres))

@main.route('/movie_selection', methods=['GET', 'POST'])
@login_required
def movie_selection():
    if request.method == 'POST':
        ratings = request.get_json()
        for movie_id, rating in ratings.items():
            existing_rating = Rating.query.filter_by(
                user_id=current_user.id,
                movie_id=movie_id
            ).first()
            
            if existing_rating:
                existing_rating.rating = rating
            else:
                new_rating = Rating(
                    user_id=current_user.id,
                    movie_id=movie_id,
                    rating=rating
                )
                db.session.add(new_rating)
        
        db.session.commit()
        
        # Generate recommendations after saving ratings
        recommender = get_recommender()
        recommendations = recommender.get_movie_recommendations(current_user.id)
        print(f"Generated {len(recommendations)} recommendations")
        
        return jsonify({'success': True, 'recommendations_generated': len(recommendations) > 0})
    
    # Get user's selected genres
    user_genres = current_user.preferred_genres.split(',') if current_user.preferred_genres else []
    print(f"User's selected genres: {user_genres}")
    
    # Get search term if provided
    search_term = request.args.get('search', '').strip().lower()
    print(f"Search term: {search_term}")
    
    # Query movies based on genres and search term
    query = Movie.query
    
    # Apply genre filtering only if genres are selected
    if user_genres and any(user_genres):  # Check if genres are selected and not empty
        genre_conditions = []
        for genre in user_genres:
            genre_conditions.append(Movie.genres.like(f'%{genre}%'))
        query = query.filter(or_(*genre_conditions))
        print(f"Number of movies after genre filtering: {query.count()}")
    
    # Apply search term filtering with improved matching
    if search_term:
        # Split search term into words and create conditions for each word
        search_words = search_term.split()
        title_conditions = []
        for word in search_words:
            title_conditions.append(Movie.title.ilike(f'%{word}%'))
        query = query.filter(or_(*title_conditions))
        print(f"Number of movies after search filtering: {query.count()}")
    
    # Get movies not yet rated by the user
    rated_movie_ids = [r.movie_id for r in Rating.query.filter_by(user_id=current_user.id).all()]
    if rated_movie_ids:
        query = query.filter(~Movie.id.in_(rated_movie_ids))
        print(f"Number of movies after removing rated movies: {query.count()}")
    
    # Get random movies with increased limit
    movies = query.order_by(func.random()).limit(50).all()
    print(f"Final number of movies to display: {len(movies)}")
    
    return render_template('movie_selection.html', movies=movies, search_term=search_term)

@main.route('/recommendations')
@login_required
def recommendations():
    # Get user's recommendations
    recommender = get_recommender()
    
    # Force recomputation of recommendations
    recommender.user_ratings = None
    recommendations = recommender.get_movie_recommendations(current_user.id)
    
    # Debug logging
    print(f"Generating recommendations for user {current_user.id}")
    print(f"Found {len(recommendations)} recommendations")
    if recommendations:
        print("Recommendation titles:")
        for movie in recommendations:
            print(f"- {movie.title}")
    
    return render_template(
        'recommendations.html',
        recommendations=recommendations,
        debug_info={
            'num_recommendations': len(recommendations) if recommendations else 0
        }
    )

@main.route('/api/movies')
@login_required
def get_movies():
    query = request.args.get('q', '')
    movies = Movie.query.filter(Movie.title.ilike(f'%{query}%')).limit(10).all()
    return jsonify([{'id': m.id, 'title': m.title} for m in movies])

@main.route('/rate_movie/<int:movie_id>', methods=['POST'])
@login_required
def rate_movie(movie_id):
    try:
        data = request.get_json()
        rating = data.get('rating')
        
        if not rating or not isinstance(rating, (int, float)) or rating < 0.5 or rating > 5.0:
            return jsonify({'success': False, 'message': 'Invalid rating value'}), 400
        
        # Check if user has already rated this movie
        existing_rating = Rating.query.filter_by(
            user_id=current_user.id,
            movie_id=movie_id
        ).first()
        
        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating
            print(f"Updated rating for user {current_user.id}, movie {movie_id} to {rating}")
        else:
            # Create new rating
            new_rating = Rating(
                user_id=current_user.id,
                movie_id=movie_id,
                rating=rating
            )
            db.session.add(new_rating)
            print(f"Created new rating for user {current_user.id}, movie {movie_id} with rating {rating}")
        
        db.session.commit()
        
        # Generate new recommendations
        recommender = get_recommender()
        recommendations = recommender.get_movie_recommendations(current_user.id)
        print(f"Generated {len(recommendations)} recommendations after rating")
        
        return jsonify({
            'success': True,
            'message': 'Rating submitted successfully!',
            'recommendations_generated': len(recommendations) > 0
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error saving rating: {str(e)}")
        return jsonify({'success': False, 'message': 'Error submitting rating'}), 500

@main.route('/search_movies')
@login_required
def search_movies():
    search_term = request.args.get('q', '').strip().lower()
    
    # Query movies based on search term only
    query = Movie.query
    
    # Apply search term filtering with improved matching
    if search_term:
        # Split search term into words and create conditions for each word
        search_words = search_term.split()
        title_conditions = []
        for word in search_words:
            title_conditions.append(Movie.title.ilike(f'%{word}%'))
        query = query.filter(or_(*title_conditions))
    
    # Get movies not yet rated by the user
    rated_movie_ids = [r.movie_id for r in Rating.query.filter_by(user_id=current_user.id).all()]
    if rated_movie_ids:
        query = query.filter(~Movie.id.in_(rated_movie_ids))
    
    # Get all matching movies
    movies = query.all()
    
    # Sort movies based on match quality
    def get_match_score(movie):
        title = movie.title.lower()
        score = 0
        
        # Exact match gets highest score
        if title == search_term:
            return 1000
        
        # Starts with search term gets high score
        if title.startswith(search_term):
            score += 500
        
        # Contains all words in order gets good score
        if all(word in title for word in search_words):
            score += 300
        
        # Contains all words in any order gets medium score
        if all(word in title for word in search_words):
            score += 200
        
        # Contains any word gets low score
        for word in search_words:
            if word in title:
                score += 50
        
        return score
    
    # Sort movies by match score
    movies.sort(key=get_match_score, reverse=True)
    
    # Take top 50 movies
    movies = movies[:50]
    
    # Debug logging
    print(f"Search term: {search_term}")
    print(f"Found {len(movies)} movies")
    for movie in movies:
        print(f"- {movie.title} (score: {get_match_score(movie)})")
    
    # Return movie data as JSON
    movie_data = [{
        'id': movie.id,
        'title': movie.title,
        'genres': movie.genres
    } for movie in movies]
    
    return jsonify(movie_data)

@main.route('/get_recommendations')
@login_required
def get_recommendations():
    # Get user's selected genres
    user_genres = current_user.preferred_genres.split(',') if current_user.preferred_genres else []
    
    # Get user's ratings
    user_ratings = Rating.query.filter_by(user_id=current_user.id).all()
    
    if not user_ratings:
        return jsonify({
            'recommendations': [],
            'message': 'Please rate some movies to get recommendations'
        })
    
    # Get movies that match user's genres
    query = Movie.query
    
    if user_genres:
        genre_conditions = []
        for genre in user_genres:
            genre_conditions.append(Movie.genres.like(f'%{genre}%'))
        query = query.filter(or_(*genre_conditions))
    
    # Get movies not yet rated by the user
    rated_movie_ids = [r.movie_id for r in user_ratings]
    if rated_movie_ids:
        query = query.filter(~Movie.id.in_(rated_movie_ids))
    
    # Get limit from request parameters, default to 10
    limit = request.args.get('limit', 10, type=int)
    
    # Get random movies from the filtered set
    movies = query.order_by(func.random()).limit(limit).all()
    
    # Return movie data as JSON
    movie_data = [{
        'id': movie.id,
        'title': movie.title,
        'genres': movie.genres
    } for movie in movies]
    
    # Customize message based on number of recommendations
    if limit == 1:
        message = 'Here is your recommended movie based on your preferences'
    else:
        message = f'Found {len(movie_data)} recommendations based on your preferences'
    
    return jsonify({
        'recommendations': movie_data,
        'message': message
    }) 