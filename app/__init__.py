from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
# from jinja2 import FileSystemBytecodeCache
import humanize

# Initialize the db object
db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder=os.path.join(os.getcwd(), 'templates'), static_folder=os.path.join(os.getcwd(), 'static'))
    
    # Register blueprints
    from app.auth.routes import auth  # Import auth blueprint
    from app.phostel.routes import phostel  # Assuming this is another blueprint

    app.register_blueprint(auth)  # Register auth blueprint
    app.register_blueprint(phostel)    # Register image blueprint

    # Safe config setup
    upload_folder = os.path.join(os.getcwd(), 'static/uploads')
    profile_folder = os.path.join(os.getcwd(), 'static/u_profiles')
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(profile_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder

    # cache_dir = os.path.join(os.getcwd(), 'jinja_cache')
    # os.makedirs(cache_dir, exist_ok=True)
    # app.jinja_env.bytecode_cache = FileSystemBytecodeCache(cache_dir)

    # App configuration for SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = '123123'
    
    db.init_app(app)
    
    # Initialize extensions
    from app.auth.routes import bcrypt, login_manager
    bcrypt.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()  # Creates tables in the database

    return app
