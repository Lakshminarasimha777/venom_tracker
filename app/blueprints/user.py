"""
User dashboard blueprint
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import current_user, login_required
from app.models import db, User, Hospital, EmergencyCase, VenomStock, Notification
from app.utils import calculate_distance, get_nearby_hospitals, get_user_location, get_snake_venom_types
from datetime import datetime, timedelta
import json

user_bp = Blueprint('user', __name__, url_prefix='/user')


def get_current_user():
    """Get current user from session"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


@user_bp.route('/dashboard')
def dashboard():
    """User dashboard"""
    user = get_current_user()
    if not user:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login_user_page'))
    
    # Get user's recent cases
    recent_cases = EmergencyCase.query.filter_by(user_id=user.id).order_by(
        EmergencyCase.created_at.desc()
    ).limit(5).all()
    
    # Get unread notifications
    unread_notifications = Notification.query.filter_by(
        user_id=user.id,
        is_read=False
    ).all()
    
    return render_template(
        'user/dashboard.html',
        user=user,
        recent_cases=recent_cases,
        unread_notifications=unread_notifications,
        venom_types=get_snake_venom_types()
    )


@user_bp.route('/find-hospitals', methods=['GET', 'POST'])
def find_hospitals():
    """Find nearby hospitals with anti-venom availability"""
    user = get_current_user()
    if not user:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login_user_page'))
    
    nearby_hospitals = []
    user_location = None
    
    if request.method == 'POST':
        # Get location from form/AJAX
        latitude = request.form.get('latitude') or request.json.get('latitude')
        longitude = request.form.get('longitude') or request.json.get('longitude')
        search_radius = float(request.form.get('radius', 50) or request.json.get('radius', 50))
        
        if latitude and longitude:
            user_location = {
                'latitude': float(latitude),
                'longitude': float(longitude),
                'district': user.district or '',
                'village': user.village or ''
            }
            
            # Get all verified active hospitals
            hospitals = Hospital.query.filter_by(is_active=True, is_verified=True).all()
            
            # Find nearby hospitals
            nearby_list = get_nearby_hospitals(user_location, hospitals, search_radius)
            
            for item in nearby_list:
                hospital = item['hospital']
                distance = item['distance']
                
                # Get venom stock info
                stocks = VenomStock.query.filter_by(hospital_id=hospital.id).all()
                stock_info = []
                total_stock = 0
                
                for stock in stocks:
                    total_stock += stock.quantity
                    stock_info.append({
                        'venom_type': stock.venom_type,
                        'quantity': stock.quantity,
                        'status': stock.get_status()
                    })
                
                nearby_hospitals.append({
                    'id': hospital.id,
                    'name': hospital.name,
                    'phone': hospital.phone,
                    'address': hospital.address,
                    'district': hospital.district,
                    'distance': distance,
                    'latitude': hospital.latitude,
                    'longitude': hospital.longitude,
                    'total_stock': total_stock,
                    'stock_info': stock_info,
                    'overall_status': hospital.overall_stock_status,
                    'is_verified': hospital.is_verified
                })
    
    if request.is_json or request.headers.get('Accept') == 'application/json':
        return jsonify(nearby_hospitals)
    
    return render_template(
        'user/find_hospitals.html',
        user=user,
        nearby_hospitals=nearby_hospitals,
        user_location=user_location,
        venom_types=get_snake_venom_types()
    )


@user_bp.route('/emergency-sos', methods=['POST'])
def emergency_sos():
    """Send emergency SOS alert"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        
        latitude = float(data.get('latitude', 0))
        longitude = float(data.get('longitude', 0))
        snake_type = data.get('snake_type', 'Unknown')
        severity = data.get('severity', 'moderate')
        description = data.get('description', '')
        location = data.get('location', '')
        
        if latitude == 0 or longitude == 0:
            return jsonify({'success': False, 'error': 'Invalid location'}), 400
        
        # Create emergency case
        emergency_case = EmergencyCase(
            user_id=user.id,
            snake_type=snake_type,
            location=location,
            latitude=latitude,
            longitude=longitude,
            severity=severity,
            description=description,
            status='pending'
        )
        
        db.session.add(emergency_case)
        db.session.commit()
        
        # Find nearest hospitals
        hospitals = Hospital.query.filter_by(is_active=True, is_verified=True).all()
        user_location = {'latitude': latitude, 'longitude': longitude}
        
        nearby = get_nearby_hospitals(user_location, hospitals, radius_km=10)[:5]
        
        # Send notifications to nearby hospitals
        for item in nearby:
            hospital = item['hospital']
            
            notification = Notification(
                hospital_id=hospital.id,
                emergency_case_id=emergency_case.id,
                type='emergency_alert',
                title=f'Emergency SOS Alert - {snake_type}',
                message=f'New emergency case at {location}. Distance: {item["distance"]} km. Severity: {severity}'
            )
            db.session.add(notification)
            
            # TODO: Send SMS/Email alerts to hospital
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Emergency alert sent to nearby hospitals',
            'case_id': emergency_case.id,
            'hospitals_notified': len(nearby)
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@user_bp.route('/update-location', methods=['POST'])
def update_location():
    """Update user location"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        
        user.latitude = float(data.get('latitude', 0))
        user.longitude = float(data.get('longitude', 0))
        user.district = data.get('district', user.district)
        user.village = data.get('village', user.village)
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Location updated'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@user_bp.route('/cases')
def cases():
    """View user's emergency cases"""
    user = get_current_user()
    if not user:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login_user_page'))
    
    # Get all user's cases with pagination
    page = request.args.get('page', 1, type=int)
    cases = EmergencyCase.query.filter_by(user_id=user.id).order_by(
        EmergencyCase.created_at.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('user/cases.html', user=user, cases=cases)


@user_bp.route('/case/<int:case_id>')
def view_case(case_id):
    """View case details"""
    user = get_current_user()
    if not user:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login_user_page'))
    
    case = EmergencyCase.query.get_or_404(case_id)
    
    # Check ownership
    if case.user_id != user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('user.cases'))
    
    return render_template('user/case_detail.html', user=user, case=case)


@user_bp.route('/notifications')
def notifications():
    """View notifications"""
    user = get_current_user()
    if not user:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login_user_page'))
    
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(user_id=user.id).order_by(
        Notification.created_at.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('user/notifications.html', user=user, notifications=notifications)


@user_bp.route('/notification/<int:notif_id>/mark-read', methods=['POST'])
def mark_notification_read(notif_id):
    """Mark notification as read"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    notification = Notification.query.get_or_404(notif_id)
    
    if notification.user_id != user.id:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})


@user_bp.route('/first-aid')
def first_aid():
    """First aid information"""
    user = get_current_user()
    return render_template('user/first_aid.html', user=user)


@user_bp.route('/settings')
def settings():
    """User settings"""
    user = get_current_user()
    if not user:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login_user_page'))
    
    return render_template('user/settings.html', user=user)


@user_bp.route('/settings/update', methods=['POST'])
def update_settings():
    """Update user settings"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        phone = request.form.get('phone', '').strip()
        district = request.form.get('district', '').strip()
        village = request.form.get('village', '').strip()
        language = request.form.get('language', 'en')
        theme = request.form.get('theme', 'light')
        
        user.phone = phone
        user.district = district
        user.village = village
        user.language_preference = language
        user.theme = theme
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Settings updated successfully', 'success')
        return redirect(url_for('user.settings'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating settings: {str(e)}', 'danger')
        return redirect(url_for('user.settings'))
