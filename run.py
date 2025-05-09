import os  # Add this import at the top
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 10000)),  # Now os is defined
        debug=False
    )
