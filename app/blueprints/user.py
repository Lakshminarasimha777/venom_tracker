"""
User dashboard blueprint
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_login import current_user, login_required
from app.models import db, User, Hospital, EmergencyCase, VenomStock, Notification
from app.utils import calculate_distance, get_nearby_hospitals, get_user_location, get_snake_venom_types, send_sms_alert, send_call_alert, send_email_alert
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

    nearby_hospitals = []
    nearby_count = 0

    def add_hospital_entry(hospital, distance=None):
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
            'is_verified': hospital.is_verified,
            'venom_types_available': hospital.get_available_venom_types()
        })

    if user.latitude is not None and user.longitude is not None:
        hospitals = Hospital.query.filter_by(is_active=True).all()
        nearby_list = get_nearby_hospitals(
            {'latitude': user.latitude, 'longitude': user.longitude},
            hospitals,
            current_app.config.get('MAX_SEARCH_RADIUS_KM', 50)
        )

        for item in nearby_list:
            hospital = item['hospital']
            if not hospital.has_venom_available():
                continue
            add_hospital_entry(hospital, distance=item['distance'])

        if not nearby_hospitals and user.district:
            hospitals = Hospital.query.filter_by(is_active=True, district=user.district).all()
            for hospital in hospitals:
                if not hospital.has_venom_available():
                    continue
                distance = calculate_distance(user.latitude, user.longitude, hospital.latitude, hospital.longitude)
                add_hospital_entry(hospital, distance=round(distance, 2))

    if not nearby_hospitals and user.district:
        hospitals = Hospital.query.filter_by(is_active=True, district=user.district).all()
        for hospital in hospitals:
            if not hospital.has_venom_available():
                continue
            add_hospital_entry(hospital)

    if not nearby_hospitals:
        hospitals = Hospital.query.filter_by(is_active=True).all()
        for hospital in hospitals:
            if not hospital.has_venom_available():
                continue
            distance = None
            if user.latitude is not None and user.longitude is not None:
                distance = round(calculate_distance(user.latitude, user.longitude, hospital.latitude, hospital.longitude), 2)
            add_hospital_entry(hospital, distance=distance)

    nearby_hospitals = sorted(nearby_hospitals, key=lambda h: (h['distance'] is None, h['distance'] if h['distance'] is not None else float('inf')))
    nearby_count = len(nearby_hospitals)

    # Add logged-in status for each hospital (logged in if last_login is within last 24 hours)
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    for hospital in nearby_hospitals:
        hospital_obj = Hospital.query.get(hospital['id'])
        hospital['is_logged_in'] = hospital_obj.last_login and hospital_obj.last_login > cutoff_time
        hospital['last_login'] = hospital_obj.last_login

    return render_template(
        'user/dashboard.html',
        user=user,
        recent_cases=recent_cases,
        unread_notifications=unread_notifications,
        venom_types=get_snake_venom_types(),
        nearby_hospitals=nearby_hospitals,
        nearby_count=nearby_count
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
            
            # Get all active hospitals, showing pending verification too
            hospitals = Hospital.query.filter_by(is_active=True).all()
            
            # Find nearby hospitals
            nearby_list = get_nearby_hospitals(user_location, hospitals, search_radius)
            
            venom_filter = request.form.get('venom_filter') or (request.json and request.json.get('venom_filter'))
            if venom_filter:
                nearby_list = [item for item in nearby_list if venom_filter in item['hospital'].get_available_venom_types()]
            
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
                    'is_verified': hospital.is_verified,
                    'venom_types_available': hospital.get_available_venom_types()
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

    user = get_current_user()
    if not user:
        return jsonify({
            'success': False,
            'error': 'Login required'
        }), 401

    try:

        data = request.get_json()

        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))

        snake_type = data.get('snake_type', 'Unknown')
        severity = data.get('severity', 'moderate')
        description = data.get('description', '')
        location = data.get('location', '')

        hospitals = Hospital.query.filter_by(
            is_active=True
        ).all()

        nearby = get_nearby_hospitals(

            {
                'latitude': latitude,
                'longitude': longitude
            },

            hospitals,

            radius_km=50

        )


        

        nearby_with_venom = []

        for item in nearby:
            hospital = item['hospital']

            # send only active hospitals
            if hospital.is_active:
                nearby_with_venom.append(item)



        hospitals_notified = 0


        for item in nearby_with_venom[:10]:

            hospital = item['hospital']


            emergency_case = EmergencyCase(

                user_id=user.id,

                hospital_id=hospital.id,

                snake_type=snake_type,

                location=location,

                latitude=latitude,

                longitude=longitude,

                severity=severity,

                description=description,

                status='pending'

            )

            db.session.add(emergency_case)
            db.session.flush()



            notification = Notification(

                hospital_id=hospital.id,

                emergency_case_id=emergency_case.id,

                type='emergency_alert',

                title=f'SOS Alert - {snake_type}',

                message=f'Snake bite reported at {location}'

            )

            db.session.add(notification)


            if hospital.phone:
                send_sms_alert(
                    hospital.phone,
                    f'Snake bite emergency at {location}'
                )

            hospitals_notified += 1


        db.session.commit()


        return jsonify({

            'success': True,

            'message': 'SOS sent successfully',

            'hospitals_notified': hospitals_notified

        })


    except Exception as e:

        db.session.rollback()

        return jsonify({

            'success': False,

            'error': str(e)

        }), 400
        
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
        
        # Find nearest hospitals (search wider radius for emergency)
        hospitals = Hospital.query.filter_by(is_active=True, is_verified=True).all()
        user_location = {'latitude': latitude, 'longitude': longitude}
        
        # Get hospitals within 50km radius for emergency
        nearby = get_nearby_hospitals(user_location, hospitals, radius_km=50)
        
        # Filter to only hospitals with venom availability and take top 10
        nearby_with_venom = [item for item in nearby if item['hospital'].has_venom_available()][:10]
        
        # If no hospitals with venom in radius, get all verified hospitals with venom (no distance limit for emergency)
        if not nearby_with_venom:
            all_hospitals = Hospital.query.filter_by(is_active=True, is_verified=True).all()
            for hospital in all_hospitals:
                if hospital.has_venom_available():
                    distance = calculate_distance(latitude, longitude, hospital.latitude, hospital.longitude)
                    nearby_with_venom.append({
                        'hospital': hospital,
                        'distance': round(distance, 2)
                    })
            nearby_with_venom = sorted(nearby_with_venom, key=lambda x: x['distance'])[:10]
        
        # Send notifications to nearby hospitals
        for item in nearby_with_venom:
            hospital = item['hospital']
            alert_message = f'New emergency case at {location}. Distance: {item["distance"]} km. Severity: {severity}.'

            notification = Notification(
                hospital_id=hospital.id,
                emergency_case_id=emergency_case.id,
                type='emergency_alert',
                title=f'Emergency SOS Alert - {snake_type}',
                message=alert_message
            )
            db.session.add(notification)

            # Send simulated SMS and call alerts to the hospital
            if hospital.phone:
                send_sms_alert(hospital.phone, alert_message)
                send_call_alert(hospital.phone, alert_message)
            if hospital.email:
                send_email_alert(hospital.email, f'Emergency Alert - {snake_type}', alert_message)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Emergency alert sent to nearby hospitals',
            'case_id': emergency_case.id,
            'hospitals_notified': len(nearby_with_venom)
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
