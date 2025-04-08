# AI-Based Movie Recommendation System

This project implements a personalized movie recommendation system using machine learning. The system suggests movies based on user preferences and viewing history.

## Features
- Collaborative filtering for movie recommendations
- Content-based filtering using movie features
- User preference analysis
- Movie similarity scoring

## Setup
1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the main script:
```bash
python movie_recommender.py
```

## Dataset
The system uses the MovieLens dataset for training and recommendations. The dataset includes:
- Movie ratings
- Movie metadata
- User preferences

## How it Works
1. The system analyzes user's past movie ratings and preferences
2. It identifies similar users and their movie preferences
3. Based on collaborative filtering, it recommends movies that similar users have enjoyed
4. The recommendations are further refined using content-based filtering

## Usage
1. Input your movie preferences and ratings
2. The system will analyze your preferences
3. Receive personalized movie recommendations 