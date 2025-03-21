"""
Flask application for Shreddit Meme Generator.
"""
import os
from flask import Flask

def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        UPLOAD_FOLDER=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp_images'),
        GENERATED_FOLDER=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generated_memes'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB max file size
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the upload and generated folders exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

    # Register blueprints
    from flask_app.routes import main
    app.register_blueprint(main.bp)

    # Make url_for('index') work
    app.add_url_rule('/', endpoint='index')

    return app 