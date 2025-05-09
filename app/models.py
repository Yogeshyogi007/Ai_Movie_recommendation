from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    preferred_genres = db.Column(db.String(255))
    
    # Relationships
    ratings = db.relationship('Rating', back_populates='user', lazy=True)
    recommendations = db.relationship('Recommendation', back_populates='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Movie(db.Model):
    __tablename__ = 'movies'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    genres = db.Column(db.String(200))
    year = db.Column(db.Integer)
    
    # Relationships
    ratings = db.relationship('Rating', back_populates='movie', lazy=True)
    recommendations = db.relationship('Recommendation', back_populates='movie', lazy=True)

    def __repr__(self):
        return f'<Movie {self.title}>'

class Rating(db.Model):
    __tablename__ = 'ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='ratings')
    movie = db.relationship('Movie', back_populates='ratings')

    def __repr__(self):
        return f'<Rating {self.user_id} -> {self.movie_id}: {self.rating}>'

class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    
    # Relationships
    user = db.relationship('User', back_populates='recommendations')
    movie = db.relationship('Movie', back_populates='recommendations')

    def __repr__(self):
        return f'<Recommendation {self.user_id} -> {self.movie_id}>'
