import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import matplotlib.pyplot as plt
import seaborn as sns

class MovieRecommender:
    def __init__(self):
        self.movies_df = None
        self.ratings_df = None
        self.user_ratings = None
        self.movie_similarity = None
        self.user_similarity = None
        
    def load_data(self, movies_path, ratings_path):
        """Load movie and rating data"""
        self.movies_df = pd.read_csv(movies_path)
        self.ratings_df = pd.read_csv(ratings_path)
        
    def preprocess_data(self):
        """Preprocess the data for recommendation"""
        # Create user-movie matrix
        self.user_ratings = self.ratings_df.pivot(
            index='userId',
            columns='movieId',
            values='rating'
        ).fillna(0)
        
        # Calculate movie similarity using cosine similarity
        self.movie_similarity = cosine_similarity(self.user_ratings.T)
        
        # Calculate user similarity
        self.user_similarity = cosine_similarity(self.user_ratings)
        
    def get_movie_recommendations(self, user_id, n_recommendations=5):
        """Get movie recommendations for a specific user"""
        if user_id not in self.user_ratings.index:
            return "User not found"
            
        # Get user's ratings
        user_ratings = self.user_ratings.loc[user_id]
        
        # Find similar users
        similar_users = self.user_similarity[user_id-1]
        similar_users_indices = similar_users.argsort()[-n_recommendations-1:-1][::-1]
        
        # Get movies rated by similar users
        similar_users_ratings = self.user_ratings.iloc[similar_users_indices]
        
        # Calculate weighted average of ratings
        weighted_ratings = np.average(
            similar_users_ratings,
            weights=similar_users[similar_users_indices],
            axis=0
        )
        
        # Get movies not rated by the user
        unrated_movies = user_ratings[user_ratings == 0].index
        
        # Get top recommendations
        recommendations = pd.Series(weighted_ratings, index=self.user_ratings.columns)
        recommendations = recommendations[unrated_movies].sort_values(ascending=False)
        
        # Get movie details
        top_recommendations = self.movies_df[self.movies_df['movieId'].isin(recommendations.head(n_recommendations).index)]
        
        return top_recommendations[['title', 'genres']]
    
    def get_similar_movies(self, movie_id, n_recommendations=5):
        """Get similar movies based on content"""
        if movie_id not in self.user_ratings.columns:
            return "Movie not found"
            
        # Get similar movies
        similar_movies = self.movie_similarity[movie_id-1]
        similar_movies_indices = similar_movies.argsort()[-n_recommendations-1:-1][::-1]
        
        # Get movie details
        similar_movies = self.movies_df[self.movies_df['movieId'].isin(similar_movies_indices)]
        
        return similar_movies[['title', 'genres']]
    
    def visualize_recommendations(self, recommendations):
        """Visualize movie recommendations"""
        plt.figure(figsize=(10, 6))
        sns.barplot(x='title', y='rating', data=recommendations)
        plt.xticks(rotation=45, ha='right')
        plt.title('Top Movie Recommendations')
        plt.tight_layout()
        plt.show()

def main():
    # Initialize the recommender
    recommender = MovieRecommender()
    
    # Load data
    print("Loading data...")
    recommender.load_data('data/movies.csv', 'data/ratings.csv')
    
    # Preprocess data
    print("Preprocessing data...")
    recommender.preprocess_data()
    
    # Get recommendations for a user
    user_id = 1  # Example user ID
    print(f"\nGetting recommendations for user {user_id}...")
    recommendations = recommender.get_movie_recommendations(user_id)
    print("\nTop Recommendations:")
    print(recommendations)
    
    # Get similar movies
    movie_id = 1  # Example movie ID
    print(f"\nGetting similar movies to movie {movie_id}...")
    similar_movies = recommender.get_similar_movies(movie_id)
    print("\nSimilar Movies:")
    print(similar_movies)

if __name__ == "__main__":
    main() 