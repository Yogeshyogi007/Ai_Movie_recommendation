from app import create_app

app = create_app()

if __name__ == '__main__':
    # Production configuration for Render
    app.run(
        host='0.0.0.0',  # Makes the server publicly available
        port=int(os.environ.get('PORT', 10000)),  # Uses Render's port or defaults to 10000
        debug=False  # Disables debug mode in production
    )
