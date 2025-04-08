from app import create_app, db
from app.models import User

def create_user():
    app = create_app()
    with app.app_context():
        # Check if user already exists
        if User.query.filter_by(email='yogeshyogi2077@gmail.com').first():
            print("User already exists!")
            return

        # Create new user
        user = User(
            username='yogesh',
            email='yogeshyogi2077@gmail.com'
        )
        user.set_password('your_password')  # Replace with your actual password
        db.session.add(user)
        db.session.commit()
        print("User created successfully!")

if __name__ == '__main__':
    create_user() 