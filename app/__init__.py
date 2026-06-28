"""Flask application factory"""

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
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load User or Admin"""

        # ---------------- USER ----------------
        try:
            if user_id.isdigit():
                return User.query.get(int(user_id))
        except:
            pass

        # ---------------- ADMIN ----------------
        try:
            if user_id.startswith("admin-"):
                admin_id = int(user_id.replace("admin-", ""))
                return Admin.query.get(admin_id)
        except:
            pass

        # ---------------- HOSPITAL (optional future support) ----------------
        try:
            if user_id.startswith("hospital-"):
                hospital_id = int(user_id.replace("hospital-", ""))
                return Hospital.query.get(hospital_id)
        except:
            pass

        return None
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(hospital_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        # Initialize default accounts on first run (helpful for fresh deployments)
        try:
            should_init = app.config.get('FLASK_ENV') != 'production' or \
                         (os.getenv('INITIALIZE_SAMPLE_DATA', '').lower() in ('1', 'true', 'yes'))

            # Create a default admin if none exist
            if should_init and not Admin.query.first():
                default_admin_username = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
                default_admin_email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@example.com')
                default_admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin123')
                admin = Admin(username=default_admin_username, email=default_admin_email)
                admin.set_password(default_admin_password)
                admin.is_super_admin = True
                db.session.add(admin)
                db.session.commit()
                app.logger.info('Default admin account created')

            # Create a demo user if none exist
            if should_init and not User.query.first():
                demo_user = User(username='farmer1', email='farmer1@example.com', phone='9876543210')
                demo_user.set_password('password123')
                db.session.add(demo_user)
                db.session.commit()
                app.logger.info('Demo user account created')

            # Create a demo hospital if none exist
            if should_init and not Hospital.query.first():
                demo_hospital = Hospital(
                    name='City Hospital',
                    email='city-hospital@example.com',
                    phone='9123456789',
                    latitude=17.6868,
                    longitude=83.2185,
                    address='Demo address',
                    district='Demo District',
                    state='Demo State',
                    pincode='000000'
                )
                demo_hospital.set_password('hospital123')
                demo_hospital.is_verified = True
                db.session.add(demo_hospital)
                db.session.commit()
                app.logger.info('Demo hospital account created')

        except Exception as e:
            try:
                db.session.rollback()
            except Exception:
                pass
            app.logger.error(f'Failed to initialize sample accounts: {e}')
    
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
