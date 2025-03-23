from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
import os

def create_app(config_class=None):
    """Application factory function that creates and configures the Flask app"""
    app = Flask(__name__)
    
    # Load configuration
    if config_class is None:
        env = os.getenv('FLASK_ENV', 'development')
        if env == 'development':
            from config import Development
            app.config.from_object(Development)
        else:
            from config import Production
            app.config.from_object(Production)
    else:
        app.config.from_object(config_class)
    
    # Initialize extensions
    from models import db
    db.init_app(app)
    
    # Configure CORS
    CORS(app, resources={
        r"/api/*": {"origins": "*"}, 
        r"/client": {"origins": "*"}, 
        r"/test_session": {"origins": "*"}
    }, supports_credentials=True)
    
    # Setup database migration
    migrate = Migrate(app, db)
    
    # Register blueprints
    from routes.admin import admin_bp
    from routes.client import client_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(client_bp)
    
    # Register API routes
    from api import setup_api
    api = setup_api(app)
    
    # Register error handlers and template filters
    register_error_handlers(app)
    register_template_filters(app)
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    return app

def register_error_handlers(app):
    """Register error handlers for the app"""
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500

def register_template_filters(app):
    """Register custom template filters"""
    from markdown import markdown
    
    @app.template_filter('markdown')
    def convert_markdown(text):
        return markdown(text, extensions=['extra', 'codehilite'])