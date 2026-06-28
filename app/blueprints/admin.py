"""
Admin dashboard blueprint
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.models import db, Admin, User, Hospital, EmergencyCase, VenomStock, Notification
from datetime import datetime, timedelta
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def get_current_admin():
    """Get current admin from session"""
    if 'admin_id' in session:
        return Admin.query.get(session['admin_id'])
    return None


@admin_bp.route('/dashboard')
def dashboard():
    """Admin dashboard"""
    admin = get_current_admin()
    if not admin:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login'))
    
    # Get statistics
    total_users = User.query.count()
    total_hospitals = Hospital.query.count()
    verified_hospitals = Hospital.query.filter_by(is_verified=True).count()
    
    # Cases today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_cases = EmergencyCase.query.filter(
        EmergencyCase.created_at >= today_start
    ).count()
    
    # Total stock
    total_stock = VenomStock.query.with_entities(
        func.sum(VenomStock.quantity)
    ).scalar() or 0
    
    # Pending hospital verifications
    pending_hospitals = Hospital.query.filter_by(is_verified=False).count()
    
    # Recent emergency cases
    recent_cases = EmergencyCase.query.order_by(
        EmergencyCase.created_at.desc()
    ).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        admin=admin,
        total_users=total_users,
        total_hospitals=total_hospitals,
        verified_hospitals=verified_hospitals,
        today_cases=today_cases,
        total_stock=total_stock,
        pending_hospitals=pending_hospitals,
        recent_cases=recent_cases
    )


@admin_bp.route('/users')
def users():
    """Manage users"""
    admin = get_current_admin()
    if not admin:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login'))
    
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.district.ilike(f'%{search}%'))
        )
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20
    )
    
    return render_template(
        'admin/users.html',
        admin=admin,
        users=users,
        search=search
    )


@admin_bp.route('/user/<int:user_id>')
def view_user(user_id):
    """View user details"""
    admin = get_current_admin()
    if not admin:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login'))
    
    user = User.query.get_or_404(user_id)
    
    # Get user's cases
    cases = EmergencyCase.query.filter_by(user_id=user.id).order_by(
        EmergencyCase.created_at.desc()
    ).limit(10).all()
    
    return render_template(
        'admin/user_detail.html',
        admin=admin,
        user=user,
        cases=cases
    )


@admin_bp.route('/user/<int:user_id>/block', methods=['POST'])
def block_user(user_id):
    """Block user"""
    admin = get_current_admin()
    if not admin:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get_or_404(user_id)
        reason = request.form.get('reason', 'No reason provided')
        
        user.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User {user.username} has been blocked'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@admin_bp.route('/user/<int:user_id>/unblock', methods=['POST'])
def unblock_user(user_id):
    """Unblock user"""
    admin = get_current_admin()
    if not admin:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get_or_404(user_id)
        user.is_active = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User {user.username} has been unblocked'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@admin_bp.route('/hospitals')
def hospitals():
    """Manage hospitals"""
    admin = get_current_admin()
    if not admin:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login'))
    
    status = request.args.get('status', 'all')  # all, verified, unverified, inactive
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = Hospital.query
    
    if status == 'verified':
        query = query.filter_by(is_verified=True)
    elif status == 'unverified':
        query = query.filter_by(is_verified=False)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    
    if search:
        query = query.filter(
            (Hospital.name.ilike(f'%{search}%')) |
            (Hospital.district.ilike(f'%{search}%'))
        )
    
    hospitals = query.order_by(Hospital.created_at.desc()).paginate(
        page=page, per_page=20
    )
    
    return render_template(
        'admin/hospitals.html',
        admin=admin,
        hospitals=hospitals,
        status=status,
        search=search
    )


@admin_bp.route('/hospital/<int:hospital_id>')
def view_hospital(hospital_id):
    """View hospital details"""
    admin = get_current_admin()
    if not admin:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login'))
    
    hospital = Hospital.query.get_or_404(hospital_id)
    
    # Get hospital's stocks
    stocks = VenomStock.query.filter_by(hospital_id=hospital.id).all()
    
    # Get hospital's cases
    cases = EmergencyCase.query.filter_by(hospital_id=hospital.id).order_by(
        EmergencyCase.created_at.desc()
    ).limit(10).all()
    
    return render_template(
        'admin/hospital_detail.html',
        admin=admin,
        hospital=hospital,
        stocks=stocks,
        cases=cases
    )


@admin_bp.route('/hospital/<int:hospital_id>/verify', methods=['POST'])
def verify_hospital(hospital_id):
    """Verify hospital"""
    admin = get_current_admin()
    if not admin:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        hospital = Hospital.query.get_or_404(hospital_id)
        hospital.is_verified = True
        hospital.updated_at = datetime.utcnow()
        
        # Send notification to hospital
        notification = Notification(
            hospital_id=hospital.id,
            type='hospital_verified',
            title='Hospital Verified',
            message='Your hospital has been verified by the admin'
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Hospital {hospital.name} has been verified'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@admin_bp.route('/hospital/<int:hospital_id>/reject', methods=['POST'])
def reject_hospital(hospital_id):
    """Reject hospital"""
    admin = get_current_admin()
    if not admin:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        hospital = Hospital.query.get_or_404(hospital_id)
        reason = request.form.get('reason', 'No reason provided')
        
        hospital.is_active = False
        hospital.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Hospital {hospital.name} has been rejected'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@admin_bp.route('/hospital/<int:hospital_id>/block', methods=['POST'])
def block_hospital(hospital_id):
    """Block hospital"""
    admin = get_current_admin()
    if not admin:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        hospital = Hospital.query.get_or_404(hospital_id)
        reason = request.form.get('reason', 'No reason provided')
        
        hospital.is_active = False
        hospital.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Hospital {hospital.name} has been blocked'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@admin_bp.route('/hospital/<int:hospital_id>/unblock', methods=['POST'])
def unblock_hospital(hospital_id):
    """Unblock hospital"""
    admin = get_current_admin()
    if not admin:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        hospital = Hospital.query.get_or_404(hospital_id)
        hospital.is_active = True
        hospital.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Hospital {hospital.name} has been unblocked'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@admin_bp.route('/hospital/add', methods=['GET', 'POST'])
def add_hospital():
    """Add new hospital"""
    admin = get_current_admin()
    if not admin:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            district = request.form.get('district', '').strip()
            state = request.form.get('state', 'Andhra Pradesh').strip()
            pincode = request.form.get('pincode', '').strip()
            latitude = float(request.form.get('latitude', 0))
            longitude = float(request.form.get('longitude', 0))
            registration_number = request.form.get('registration_number', '').strip()
            license_number = request.form.get('license_number', '').strip()
            
            if not all([name, email, password, phone, address, district, pincode]):
                flash('All required fields must be filled', 'danger')
                return redirect(url_for('admin.add_hospital'))
            
            if Hospital.query.filter_by(name=name).first():
                flash('Hospital name already exists', 'danger')
                return redirect(url_for('admin.add_hospital'))
            
            if Hospital.query.filter_by(email=email).first():
                flash('Email already registered', 'danger')
                return redirect(url_for('admin.add_hospital'))
            
            hospital = Hospital(
                name=name,
                email=email,
                phone=phone,
                address=address,
                district=district,
                state=state,
                pincode=pincode,
                latitude=latitude,
                longitude=longitude,
                registration_number=registration_number,
                license_number=license_number,
                is_verified=True,
                is_active=True
            )
            hospital.set_password(password)
            
            db.session.add(hospital)
            db.session.commit()
            
            flash(f'Hospital {name} added successfully', 'success')
            return redirect(url_for('admin.view_hospital', hospital_id=hospital.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding hospital: {str(e)}', 'danger')
            return redirect(url_for('admin.add_hospital'))
    
    from app.utils import get_districts_list
    districts = get_districts_list()
    return render_template('admin/add_hospital.html', admin=admin, districts=districts)


@admin_bp.route('/hospital/<int:hospital_id>/edit', methods=['GET', 'POST'])
def edit_hospital(hospital_id):
    """Edit hospital"""
    admin = get_current_admin()
    if not admin:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login'))
    
    hospital = Hospital.query.get_or_404(hospital_id)
    
    if request.method == 'POST':
        try:
            hospital.name = request.form.get('name', '').strip()
            hospital.email = request.form.get('email', '').strip()
            hospital.phone = request.form.get('phone', '').strip()
            hospital.address = request.form.get('address', '').strip()
            hospital.district = request.form.get('district', '').strip()
            hospital.state = request.form.get('state', '').strip()
            hospital.pincode = request.form.get('pincode', '').strip()
            hospital.latitude = float(request.form.get('latitude', hospital.latitude))
            hospital.longitude = float(request.form.get('longitude', hospital.longitude))
            hospital.registration_number = request.form.get('registration_number', '').strip()
            hospital.license_number = request.form.get('license_number', '').strip()
            
            password = request.form.get('password', '')
            if password:
                hospital.set_password(password)
            
            hospital.updated_at = datetime.utcnow()
            db.session.commit()
            
            flash(f'Hospital {hospital.name} updated successfully', 'success')
            return redirect(url_for('admin.view_hospital', hospital_id=hospital.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating hospital: {str(e)}', 'danger')
            return redirect(url_for('admin.edit_hospital', hospital_id=hospital_id))
    
    from app.utils import get_districts_list
    districts = get_districts_list()
    return render_template('admin/edit_hospital.html', admin=admin, hospital=hospital, districts=districts)


@admin_bp.route('/hospital/<int:hospital_id>/delete', methods=['POST'])
def delete_hospital(hospital_id):
    """Delete hospital"""
    admin = get_current_admin()
    if not admin:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        hospital = Hospital.query.get_or_404(hospital_id)
        hospital_name = hospital.name
        
        # Delete related venom stocks
        VenomStock.query.filter_by(hospital_id=hospital.id).delete()
        
        # Delete related emergency cases
        EmergencyCase.query.filter_by(hospital_id=hospital.id).delete()
        
        # Delete related notifications
        Notification.query.filter_by(hospital_id=hospital.id).delete()
        
        # Delete hospital
        db.session.delete(hospital)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Hospital {hospital_name} has been deleted',
            'redirect': url_for('admin.hospitals')
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@admin_bp.route('/emergency-cases')
def emergency_cases():
    """View all emergency cases"""
    admin = get_current_admin()
    if not admin:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login'))
    
    status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    
    query = EmergencyCase.query
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    cases = query.order_by(EmergencyCase.created_at.desc()).paginate(
        page=page, per_page=20
    )
    
    return render_template(
        'admin/emergency_cases.html',
        admin=admin,
        cases=cases,
        status=status
    )


@admin_bp.route('/analytics')
def analytics():
    """Analytics dashboard"""
    admin = get_current_admin()
    if not admin:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login'))
    
    # Get statistics for different time periods
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = datetime.utcnow() - timedelta(days=7)
    month_start = datetime.utcnow() - timedelta(days=30)
    
    # Today's cases
    today_cases = EmergencyCase.query.filter(
        EmergencyCase.created_at >= today_start
    ).count()
    
    # This week's cases
    week_cases = EmergencyCase.query.filter(
        EmergencyCase.created_at >= week_start
    ).count()
    
    # This month's cases
    month_cases = EmergencyCase.query.filter(
        EmergencyCase.created_at >= month_start
    ).count()
    
    # Cases by district (most affected)
    district_stats = db.session.query(
        EmergencyCase.location,
        func.count(EmergencyCase.id)
    ).filter(
        EmergencyCase.created_at >= month_start
    ).group_by(EmergencyCase.location).order_by(
        func.count(EmergencyCase.id).desc()
    ).limit(10).all()
    
    # Stock availability by district
    hospital_stock = db.session.query(
        Hospital.district,
        func.sum(VenomStock.quantity),
        func.count(Hospital.id)
    ).join(VenomStock, Hospital.id == VenomStock.hospital_id).group_by(
        Hospital.district
    ).all()
    
    return render_template(
        'admin/analytics.html',
        admin=admin,
        today_cases=today_cases,
        week_cases=week_cases,
        month_cases=month_cases,
        district_stats=district_stats,
        hospital_stock=hospital_stock
    )


@admin_bp.route('/settings')
def settings():
    """Admin settings"""
    admin = get_current_admin()
    if not admin:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login'))
    
    return render_template('admin/settings.html', admin=admin)


@admin_bp.route('/settings/update', methods=['POST'])
def update_settings():
    """Update admin settings"""
    admin = get_current_admin()
    if not admin:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        email = request.form.get('email', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        
        if not admin.check_password(current_password):
            return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
        
        admin.email = email
        
        if new_password:
            if len(new_password) < 6:
                return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
            admin.set_password(new_password)
        
        admin.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Settings updated successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
