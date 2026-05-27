"""
Authentication blueprint for Venom_Tracker
User, Hospital, Admin login & registration
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user
from datetime import datetime
import json

from app.models import db, User, Hospital, Admin
from app.utils import get_districts_list, get_snake_venom_types, get_states_list

auth_bp = Blueprint('auth', __name__)


# =========================
# USER REGISTER
# =========================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone = request.form.get('phone', '').strip()
        district = request.form.get('district', '').strip()

        if not all([username, email, password, phone]):
            flash('All fields are required', 'danger')
            return redirect(url_for('auth.register_user'))

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.register_user'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('auth.register_user'))

        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('auth.register_user'))

        try:
            user = User(
                username=username,
                email=email,
                phone=phone,
                district=district
            )
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
            return redirect(url_for('auth.register_user'))

    return render_template('auth/register.html')


# =========================
# LOGIN (USER / HOSPITAL / ADMIN)
# =========================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user_type = request.form.get('user_type', 'user')

        if not username or not password:
            flash('Enter username and password', 'danger')
            return redirect(url_for('auth.login'))

        try:
            # ---------------- USER LOGIN ----------------
            if user_type == 'user':
                user = User.query.filter_by(username=username).first()

                if user and user.check_password(password) and user.is_active:
                    login_user(user)
                    session['user_type'] = 'user'
                    session['user_id'] = user.id
                    return redirect(url_for('user.dashboard'))

            # ---------------- HOSPITAL LOGIN ----------------
            elif user_type == 'hospital':
                hospital = Hospital.query.filter_by(email=username).first()

                if hospital and hospital.check_password(password) and hospital.is_active:
                    hospital.last_login = datetime.utcnow()
                    db.session.commit()

                    session['user_type'] = 'hospital'
                    session['hospital_id'] = hospital.id
                    return redirect(url_for('hospital.dashboard'))

            # ---------------- ADMIN LOGIN ----------------
            elif user_type == 'admin':
                admin = Admin.query.filter_by(username=username).first()

                if admin and admin.check_password(password) and admin.is_active:
                    login_user(admin)
                    session['user_type'] = 'admin'
                    session['admin_id'] = admin.id
                    return redirect(url_for('admin.dashboard'))

            flash('Invalid credentials or inactive account', 'danger')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash(f'Login error: {str(e)}', 'danger')
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')


# =========================
# HOSPITAL REGISTER
# =========================
@auth_bp.route('/hospital-register', methods=['GET', 'POST'])
def register_hospital():
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

        venom_types = request.form.getlist('venom_types')

        if not all([name, email, password, phone, address, district]):
            flash('All fields are required', 'danger')
            return redirect(url_for('auth.register_hospital'))

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.register_hospital'))

        if Hospital.query.filter_by(name=name).first():
            flash('Hospital already exists', 'danger')
            return redirect(url_for('auth.register_hospital'))

        if Hospital.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('auth.register_hospital'))

        try:
            hospital = Hospital(
                name=name,
                email=email,
                phone=phone,
                address=address,
                district=district,
                state=state,
                pincode=pincode,
                venom_types_available=json.dumps(venom_types)
            )
            hospital.set_password(password)

            db.session.add(hospital)
            db.session.commit()

            flash('Hospital registered successfully. Await admin approval.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
            return redirect(url_for('auth.register_hospital'))

    districts = get_districts_list()
    venom_types = get_snake_venom_types()
    states = get_states_list()

    return render_template(
        'auth/register_hospital.html',
        districts=districts,
        venom_types=venom_types,
        states=states
    )


# =========================
# LOGOUT
# =========================
@auth_bp.route('/logout')
def logout():
    logout_user()
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('auth.login'))
