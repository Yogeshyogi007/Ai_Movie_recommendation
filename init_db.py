from app import create_app, db
from app.models import User, Movie, Rating, Recommendation
import pandas as pd
from sqlalchemy.exc import IntegrityError

def init_db():
    app = create_app()
    with app.app_context():
        # Drop all tables and recreate them
        print("Dropping existing tables...")
        db.drop_all()
        print("Creating new tables...")
        db.create_all()
        
        # Load movies data
        print("Loading movies data...")
        movies_df = pd.read_csv('data/movies.csv')
        total_movies = len(movies_df)
        for i, (_, row) in enumerate(movies_df.iterrows(), 1):
            try:
                movie = Movie(
                    id=row['movieId'],
                    title=row['title'],
                    genres=row['genres']
                )
                db.session.add(movie)
                if i % 100 == 0:
                    print(f"Processed {i}/{total_movies} movies")
                    db.session.commit()
            except IntegrityError:
                db.session.rollback()
                continue
        db.session.commit()
        print("Movies loaded successfully!")
        
        # Create a test user
        print("Creating test user...")
        test_user = User(
            username='test_user',
            email='test@example.com'
        )
        test_user.set_password('password123')
        db.session.add(test_user)
        db.session.commit()
        
        # Load ratings data (only first 1000 ratings for testing)
        print("Loading ratings data...")
        ratings_df = pd.read_csv('data/ratings.csv')
        ratings_df = ratings_df.head(1000)  # Limit to first 1000 ratings for testing
        total_ratings = len(ratings_df)
        
        for i, (_, row) in enumerate(ratings_df.iterrows(), 1):
            try:
                # Create a user for each unique user_id in the ratings
                user = db.session.get(User, row['userId'])
                if not user:
                    user = User(
                        username=f'user_{row["userId"]}',
                        email=f'user_{row["userId"]}@example.com'
                    )
                    user.set_password('password123')
                    db.session.add(user)
                    db.session.commit()
                
                rating = Rating(
                    user_id=row['userId'],
                    movie_id=row['movieId'],
                    rating=row['rating']
                )
                db.session.add(rating)
                if i % 100 == 0:
                    print(f"Processed {i}/{total_ratings} ratings")
                    db.session.commit()
            except IntegrityError:
                db.session.rollback()
                continue
        
        db.session.commit()
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_db() 