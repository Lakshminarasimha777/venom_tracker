"""
Authentication blueprint for user registration and login
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, current_user
from app.models import db, User, Hospital, Admin
from app.utils import get_districts_list, get_snake_venom_types, get_states_list
from werkzeug.security import generate_password_hash
from datetime import datetime
import json

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register_user():
    """User registration page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone = request.form.get('phone', '').strip()
        district = request.form.get('district', '').strip()
        
        # Validation
        if not all([username, email, password, phone]):
            flash('All fields are required', 'danger')
            return redirect(url_for('auth.register_user'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return redirect(url_for('auth.register_user'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.register_user'))
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('auth.register_user'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register_user'))
        
        try:
            # Create new user
            user = User(
                username=username,
                email=email,
                phone=phone,
                district=district
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login_user'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
            return redirect(url_for('auth.register_user'))
    
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login_user_page():
    """User login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user_type = request.form.get('user_type', 'user')  # user, hospital, admin
        
        if not all([username, password]):
            flash('Username and password required', 'danger')
            return redirect(url_for('auth.login_user_page'))
        
        try:
            if user_type == 'user':
                user = User.query.filter_by(username=username).first()
                if user and user.check_password(password) and user.is_active:
                    login_user(user, remember=True)
                    session['user_id'] = user.id
                    session['user_type'] = 'user'
                    flash(f'Welcome back, {user.username}!', 'success')
                    return redirect(url_for('user.dashboard'))
            
            elif user_type == 'hospital':
                hospital = Hospital.query.filter_by(username=username).first() if hasattr(Hospital, 'username') else None
                if not hospital:
                    hospital = Hospital.query.filter_by(email=username).first()
                
                if hospital and hospital.check_password(password) and hospital.is_active:
                    hospital.last_login = datetime.utcnow()
                    db.session.commit()
                    session['hospital_id'] = hospital.id
                    session['user_type'] = 'hospital'
                    flash(f'Welcome back, {hospital.name}!', 'success')
                    return redirect(url_for('hospital.dashboard'))
            
            elif user_type == 'admin':
                admin = Admin.query.filter_by(username=username).first()
                
                if admin and admin.check_password(password) and admin.is_active:
                    session['admin_id'] = admin.id
                    session['user_type'] = 'admin'
                    flash(f'Welcome back, {admin.username}!', 'success')
                    return redirect(url_for('admin.dashboard'))
            
            flash('Invalid credentials or account inactive', 'danger')
            return redirect(url_for('auth.login_user_page'))
        
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'danger')
            return redirect(url_for('auth.login_user_page'))
    
    return render_template('auth/login.html')


@auth_bp.route('/hospital-register', methods=['GET', 'POST'])
def register_hospital():
    """Hospital registration page"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        district = request.form.get('district', '').strip()
        state = request.form.get('state', 'Andhra Pradesh').strip()
        pincode = request.form.get('pincode', '').strip()
        latitude = request.form.get('latitude', '').strip()
        longitude = request.form.get('longitude', '').strip()
        registration_number = request.form.get('registration_number', '').strip()
        license_number = request.form.get('license_number', '').strip()
        
        # Get selected venom types
        venom_types = request.form.getlist('venom_types')
        
        def parse_coordinate(value):
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.0
        
        # Validation
        if not all([name, email, password, phone, address, district]):
            flash('All fields are required', 'danger')
            return redirect(url_for('auth.register_hospital'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return redirect(url_for('auth.register_hospital'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.register_hospital'))
        
        # Check if hospital exists
        if Hospital.query.filter_by(name=name).first():
            flash('Hospital already registered', 'danger')
            return redirect(url_for('auth.register_hospital'))
        
        if Hospital.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register_hospital'))
        
        try:
            # Create new hospital
            hospital = Hospital(
                name=name,
                email=email,
                phone=phone,
                address=address,
                district=district,
                state=state,
                pincode=pincode,
                latitude=parse_coordinate(latitude),
                longitude=parse_coordinate(longitude),
                registration_number=registration_number,
                license_number=license_number,
                venom_types_available=json.dumps(venom_types) if venom_types else json.dumps([])
            )
            hospital.set_password(password)
            
            db.session.add(hospital)
            db.session.commit()
            
            flash('Hospital registration successful! Waiting for admin verification.', 'success')
            return redirect(url_for('auth.login_user_page'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
            return redirect(url_for('auth.register_hospital'))
    
    districts = get_districts_list()
    venom_types = get_snake_venom_types()
    states = get_states_list()
    return render_template('auth/register_hospital.html', districts=districts, venom_types=venom_types, states=states)


@auth_bp.route('/logout')
def logout():
    """Logout route"""
    logout_user()
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))
