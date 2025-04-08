import pandas as pd
from app import db
from app.models import Rating, Movie, User, Recommendation
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from flask import current_app
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import or_

class MovieRecommender:
    def __init__(self):
        self.user_ratings = None
        self.movie_similarity = None
        self.user_similarity = None
        # Don't call preprocess_data here, it will be called when needed

    def preprocess_data(self):
        """Preprocess the data for recommendation"""
        # Get all ratings from the database
        ratings = Rating.query.all()
        
        if not ratings:
            print("No ratings found in the database")
            return False
            
        # Convert to DataFrame
        ratings_data = []
        for rating in ratings:
            ratings_data.append({
                'user_id': rating.user_id,
                'movie_id': rating.movie_id,
                'rating': rating.rating
            })
        
        ratings_df = pd.DataFrame(ratings_data)
        
        # Debug logging
        print(f"Found {len(ratings_df)} total ratings")
        print(f"Unique users: {ratings_df['user_id'].nunique()}")
        print(f"Unique movies: {ratings_df['movie_id'].nunique()}")
        
        # Handle duplicate ratings by taking the average
        ratings_df = ratings_df.groupby(['user_id', 'movie_id'])['rating'].mean().reset_index()
        
        # Create user-movie rating matrix
        self.user_ratings = ratings_df.pivot(
            index='user_id',
            columns='movie_id',
            values='rating'
        ).fillna(0)
        
        # Debug logging
        print(f"User-movie matrix shape: {self.user_ratings.shape}")
        
        # Calculate movie similarity matrix
        self.movie_similarity = cosine_similarity(self.user_ratings.T)
        
        # Calculate user similarity
        self.user_similarity = cosine_similarity(self.user_ratings)
        
        return True

    def get_movie_recommendations(self, user_id, n_recommendations=10):
        """Get movie recommendations for a specific user"""
        print(f"\nGenerating recommendations for user {user_id}")
        
        if self.user_ratings is None:
            print("Preprocessing data...")
            if not self.preprocess_data():
                print("No ratings found in database")
                return []
        
        if user_id not in self.user_ratings.index:
            print(f"User {user_id} not found in ratings matrix")
            return []
        
        # Get user's ratings
        user_ratings = self.user_ratings.loc[user_id]
        print(f"User {user_id} has rated {len(user_ratings[user_ratings > 0])} movies")
        
        # Get user's preferred genres
        user = User.query.get(user_id)
        preferred_genres = set(user.preferred_genres.split(',')) if user.preferred_genres else set()
        print(f"User's preferred genres: {preferred_genres}")
        
        # Get unrated movies
        unrated_movies = user_ratings[user_ratings == 0].index
        
        # Get movies that match user's preferred genres
        if preferred_genres:
            genre_movies = Movie.query.filter(
                or_(*[Movie.genres.like(f'%{genre}%') for genre in preferred_genres])
            ).all()
            genre_movie_ids = {movie.id for movie in genre_movies}
            unrated_movies = [mid for mid in unrated_movies if mid in genre_movie_ids]
        
        print(f"Found {len(unrated_movies)} unrated movies matching preferences")
        
        if len(unrated_movies) == 0:
            print("No unrated movies found")
            return []
        
        # Calculate predicted ratings for unrated movies
        predicted_ratings = []
        for movie_id in unrated_movies:
            if movie_id in self.user_ratings.columns:
                # Get similarity scores for this movie
                movie_similarity = self.movie_similarity[self.user_ratings.columns.get_loc(movie_id)]
                
                # Get ratings for movies the user has rated
                rated_movies = user_ratings[user_ratings > 0].index
                if len(rated_movies) > 0:
                    # Get similarity scores for rated movies
                    rated_movie_indices = [self.user_ratings.columns.get_loc(mid) for mid in rated_movies if mid in self.user_ratings.columns]
                    if rated_movie_indices:
                        similarity_scores = movie_similarity[rated_movie_indices]
                        user_ratings_for_rated = user_ratings[rated_movies]
                        
                        # Calculate weighted average
                        if np.sum(similarity_scores) > 0:
                            predicted_rating = np.sum(similarity_scores * user_ratings_for_rated) / np.sum(similarity_scores)
                            predicted_ratings.append((movie_id, predicted_rating))
        
        print(f"Calculated predicted ratings for {len(predicted_ratings)} movies")
        
        # Sort by predicted rating and get top recommendations
        predicted_ratings.sort(key=lambda x: x[1], reverse=True)
        recommended_movie_ids = [movie_id for movie_id, _ in predicted_ratings[:n_recommendations]]
        print(f"Top {len(recommended_movie_ids)} recommended movie IDs: {recommended_movie_ids}")
        
        # Get movie details from database
        recommended_movies = Movie.query.filter(Movie.id.in_(recommended_movie_ids)).all()
        print(f"Found {len(recommended_movies)} movie details in database")
        
        # Sort movies to match the order of recommended_movie_ids
        movie_dict = {movie.id: movie for movie in recommended_movies}
        recommendations = [movie_dict[movie_id] for movie_id in recommended_movie_ids if movie_id in movie_dict]
        print(f"Returning {len(recommendations)} recommendations")
        
        # Save recommendations to database
        try:
            # Delete old recommendations
            Recommendation.query.filter_by(user_id=user_id).delete()
            
            # Save new recommendations
            for movie_id, score in predicted_ratings[:n_recommendations]:
                recommendation = Recommendation(
                    user_id=user_id,
                    movie_id=movie_id,
                    score=score
                )
                db.session.add(recommendation)
            
            db.session.commit()
            print("Successfully saved recommendations to database")
        except Exception as e:
            db.session.rollback()
            print(f"Error saving recommendations: {str(e)}")
        
        return recommendations
    
    def get_similar_movies(self, movie_id, n_recommendations=5):
        """Get similar movies based on content"""
        if self.movie_similarity is None:
            self.preprocess_data()
            
        if movie_id not in self.user_ratings.columns:
            return []
            
        # Get similar movies
        similar_movies = self.movie_similarity[movie_id-1]
        similar_movies_indices = similar_movies.argsort()[-n_recommendations-1:-1][::-1]
        
        # Get movie details from database
        similar_movies = []
        for idx in similar_movies_indices:
            movie = Movie.query.get(idx + 1)  # +1 because movie IDs start from 1
            if movie:
                similar_movies.append(movie)
        
        return similar_movies 