"""
Shreddit Meme Generator Flask App Entry Point
"""
import os
from dotenv import load_dotenv
from flask_app import create_app

# Load environment variables
load_dotenv()

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Run the app in debug mode if not in production
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=5000) 