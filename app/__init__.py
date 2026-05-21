"""
Flask application factory
"""

import os
from flask import Flask, render_template, redirect, url_for, session
from flask_login import LoginManager
from config import config_by_name
from app.models import db, User, Hospital, Admin
from app.blueprints.auth import auth_bp
from app.blueprints.user import user_bp
from app.blueprints.hospital import hospital_bp
from app.blueprints.admin import admin_bp
from app.blueprints.api import api_bp


def create_app(config_name='development'):
    """Application factory function"""
    
    # Determine project root to locate root-level templates and static folders
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # Create Flask app with explicit template and static folder paths
    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, 'templates'),
        static_folder=os.path.join(project_root, 'static')
    )
    
    # Load configuration
    config = config_by_name.get(config_name, config_by_name['development'])
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login_user_page'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID"""
        return User.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(hospital_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Index route
    @app.route('/')
    def index():
        """Home page"""
        return render_template('index.html')
    
    @app.route('/about')
    def about():
        """About page"""
        return render_template('about.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """404 error handler"""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """500 error handler"""
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        """403 error handler"""
        return render_template('errors/403.html'), 403
    
    # Context processor for injecting data into templates
    @app.context_processor
    def inject_user():
        """Inject user info into all templates"""
        return {
            'is_admin_logged_in': 'admin_id' in session,
            'is_hospital_logged_in': 'hospital_id' in session
        }
    
    return app
