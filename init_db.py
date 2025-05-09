from app import create_app, db
from app.models import User, Movie, Rating, Recommendation
import pandas as pd
from sqlalchemy.exc import IntegrityError, OperationalError
import time

def init_db():
    app = create_app()
    
    with app.app_context():
        # Retry logic for database connection
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1} of {max_retries} to initialize database...")
                
                # Drop all tables and recreate them
                print("Dropping existing tables...")
                db.drop_all()
                print("Creating new tables...")
                db.create_all()
                
                # Verify tables exist before loading data
                if not db.engine.has_table('users'):
                    raise OperationalError("Users table not created")
                
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
                            db.session.commit()
                            print(f"Processed {i}/{total_movies} movies")
                    except IntegrityError:
                        db.session.rollback()
                        continue
                
                db.session.commit()
                print("Movies loaded successfully!")
                
                # Create test users
                print("Creating test users...")
                test_users = [
                    {'username': 'test_user', 'email': 'test@example.com', 'password': 'password123'},
                    {'username': 'admin', 'email': 'admin@example.com', 'password': 'admin123'}
                ]
                
                for user_data in test_users:
                    if not User.query.filter_by(email=user_data['email']).first():
                        user = User(
                            username=user_data['username'],
                            email=user_data['email']
                        )
                        user.set_password(user_data['password'])
                        db.session.add(user)
                
                db.session.commit()
                print("Test users created successfully!")
                
                # Load sample ratings
                print("Loading sample ratings...")
                ratings_df = pd.read_csv('data/ratings.csv').head(1000)
                
                for _, row in ratings_df.iterrows():
                    try:
                        rating = Rating(
                            user_id=row['userId'],
                            movie_id=row['movieId'],
                            rating=row['rating']
                        )
                        db.session.add(rating)
                    except IntegrityError:
                        db.session.rollback()
                        continue
                
                db.session.commit()
                print("Database initialized successfully!")
                return  # Success!
                
            except OperationalError as e:
                print(f"Database error: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print("Max retries reached. Failed to initialize database.")
                    raise

if __name__ == '__main__':
    init_db()
