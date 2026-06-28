"""
Hospital dashboard blueprint
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.models import db, Hospital, VenomStock, EmergencyCase, Notification
from app.utils import get_snake_venom_types
from datetime import datetime, timedelta
from sqlalchemy import func, or_
import json

hospital_bp = Blueprint('hospital', __name__, url_prefix='/hospital')


def get_current_hospital():
    """Get current hospital from session"""
    if 'hospital_id' in session:
        return Hospital.query.get(session['hospital_id'])
    return None


@hospital_bp.route('/dashboard')
def dashboard():
    """Hospital dashboard"""
    hospital = get_current_hospital()
    if not hospital:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login'))
    
    # Get statistics
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_cases = EmergencyCase.query.filter_by(hospital_id=hospital.id).filter(
        EmergencyCase.created_at >= today_start
    ).count()
    
    total_stock = VenomStock.query.filter_by(hospital_id=hospital.id).with_entities(
        func.sum(VenomStock.quantity)
    ).scalar() or 0
    
    pending_cases = EmergencyCase.query.filter_by(
        hospital_id=hospital.id,
        status='pending'
    ).count()
    
    # Get pending notifications
    pending_notifications = Notification.query.filter_by(
        hospital_id=hospital.id,
        is_read=False
    ).all()
    
    # Get recent emergency cases and incoming notified cases
    notified_rows = db.session.query(Notification.emergency_case_id).filter_by(
        hospital_id=hospital.id,
        type='emergency_alert'
    ).all()
    notified_case_ids = [row[0] for row in notified_rows if row and row[0]]

    recent_cases = EmergencyCase.query.filter(
        or_(
            EmergencyCase.hospital_id == hospital.id,
            EmergencyCase.id.in_(notified_case_ids)
        )
    ).order_by(
        EmergencyCase.created_at.desc()
    ).limit(5).all()
    
    return render_template(
        'hospital/dashboard.html',
        hospital=hospital,
        today_cases=today_cases,
        total_stock=total_stock,
        pending_cases=pending_cases,
        pending_notifications=pending_notifications,
        recent_cases=recent_cases,
        venom_types=get_snake_venom_types()
    )


@hospital_bp.route('/stock')
def stock():
    """Manage anti-venom stock"""
    hospital = get_current_hospital()
    if not hospital:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login'))
    
    stocks = VenomStock.query.filter_by(hospital_id=hospital.id).all()
    
    return render_template('hospital/stock.html', hospital=hospital, stocks=stocks)


@hospital_bp.route('/stock/add', methods=['POST'])
def add_stock():
    """Add anti-venom stock"""
    hospital = get_current_hospital()
    if not hospital:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        venom_type = request.form.get('venom_type', '').strip()
        quantity = int(request.form.get('quantity', 0))
        minimum_threshold = int(request.form.get('minimum_threshold', 5))
        
        if quantity < 0 or minimum_threshold < 0:
            return jsonify({'success': False, 'error': 'Invalid quantity'}), 400
        
        # Check if stock already exists
        stock = VenomStock.query.filter_by(
            hospital_id=hospital.id,
            venom_type=venom_type
        ).first()
        
        if stock:
            stock.quantity = quantity
            stock.minimum_threshold = minimum_threshold
            stock.last_updated = datetime.utcnow()
            stock.updated_by = hospital.name
        else:
            stock = VenomStock(
                hospital_id=hospital.id,
                venom_type=venom_type,
                quantity=quantity,
                minimum_threshold=minimum_threshold,
                updated_by=hospital.name
            )
            db.session.add(stock)
        
        # Update hospital overall stock status
        total_stock = sum(s.quantity for s in hospital.venom_stocks.all())
        if total_stock == 0:
            hospital.overall_stock_status = 'critical'
        elif total_stock <= 10:
            hospital.overall_stock_status = 'low'
        else:
            hospital.overall_stock_status = 'good'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Stock updated successfully',
            'stock_id': stock.id
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@hospital_bp.route('/update-venom-availability', methods=['POST'])
def update_venom_availability():
    """Update hospital venom availability status"""
    hospital = get_current_hospital()
    if not hospital:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        venom_types = request.form.getlist('venom_types')
        hospital.set_available_venom_types(venom_types)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Venom availability updated successfully',
            'venom_types': venom_types
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@hospital_bp.route('/stock/<int:stock_id>/update-quantity', methods=['POST'])
def update_stock_quantity(stock_id):
    """Update stock quantity"""
    hospital = get_current_hospital()
    if not hospital:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        stock = VenomStock.query.get_or_404(stock_id)
        
        if stock.hospital_id != hospital.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        quantity = int(request.form.get('quantity', 0))
        
        if quantity < 0:
            return jsonify({'success': False, 'error': 'Invalid quantity'}), 400
        
        stock.quantity = quantity
        stock.last_updated = datetime.utcnow()
        stock.updated_by = hospital.name
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Stock quantity updated',
            'quantity': quantity
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@hospital_bp.route('/emergency-cases')
def emergency_cases():
    """View incoming emergency cases"""
    hospital = get_current_hospital()
    if not hospital:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login'))
    
    status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    
    query = EmergencyCase.query.filter_by(hospital_id=hospital.id)
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    cases = query.order_by(EmergencyCase.created_at.desc()).paginate(
        page=page, per_page=10
    )
    
    return render_template(
        'hospital/emergency_cases.html',
        hospital=hospital,
        cases=cases,
        current_status=status
    )


@hospital_bp.route('/case/<int:case_id>')
def view_case(case_id):
    """View case details"""
    hospital = get_current_hospital()
    if not hospital:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login'))
    
    case = EmergencyCase.query.get_or_404(case_id)
    
    if case.hospital_id != hospital.id:
        flash('Access denied', 'danger')
        return redirect(url_for('hospital.emergency_cases'))
    
    return render_template('hospital/case_detail.html', hospital=hospital, case=case)


@hospital_bp.route('/case/<int:case_id>/accept', methods=['POST'])
def accept_case(case_id):
    """Accept emergency case"""
    hospital = get_current_hospital()
    if not hospital:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        case = EmergencyCase.query.get_or_404(case_id)
        
        if case.hospital_id != hospital.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        case.status = 'accepted'
        case.hospital_response_time = datetime.utcnow()
        case.updated_at = datetime.utcnow()
        
        # Notify user
        notification = Notification(
            user_id=case.user_id,
            emergency_case_id=case.id,
            type='case_accepted',
            title='Emergency Case Accepted',
            message=f'{hospital.name} has accepted your emergency case.'
        )
        db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Case accepted successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@hospital_bp.route('/case/<int:case_id>/reject', methods=['POST'])
def reject_case(case_id):
    """Reject emergency case"""
    hospital = get_current_hospital()
    if not hospital:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        case = EmergencyCase.query.get_or_404(case_id)
        
        if case.hospital_id != hospital.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        reason = request.form.get('reason', 'No reason provided')
        
        case.status = 'rejected'
        case.medical_notes = reason
        case.updated_at = datetime.utcnow()
        
        # Notify user
        notification = Notification(
            user_id=case.user_id,
            emergency_case_id=case.id,
            type='case_rejected',
            title='Emergency Case Rejected',
            message=f'{hospital.name} has rejected your emergency case.'
        )
        db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Case rejected'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@hospital_bp.route('/case/<int:case_id>/complete', methods=['POST'])
def complete_case(case_id):
    """Complete emergency case"""
    hospital = get_current_hospital()
    if not hospital:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        case = EmergencyCase.query.get_or_404(case_id)
        
        if case.hospital_id != hospital.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        notes = request.form.get('notes', '')
        
        case.status = 'completed'
        case.medical_notes = notes
        case.updated_at = datetime.utcnow()
        
        # Notify user
        notification = Notification(
            user_id=case.user_id,
            emergency_case_id=case.id,
            type='case_completed',
            title='Emergency Case Completed',
            message=f'Your emergency case at {hospital.name} has been completed.'
        )
        db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Case marked as completed'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@hospital_bp.route('/analytics')
def analytics():
    """Hospital analytics"""
    hospital = get_current_hospital()
    if not hospital:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login'))
    
    # Get 30-day statistics
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Cases by status
    total_cases = EmergencyCase.query.filter_by(hospital_id=hospital.id).filter(
        EmergencyCase.created_at >= thirty_days_ago
    ).count()
    
    accepted_cases = EmergencyCase.query.filter_by(
        hospital_id=hospital.id,
        status='accepted'
    ).filter(EmergencyCase.created_at >= thirty_days_ago).count()
    
    completed_cases = EmergencyCase.query.filter_by(
        hospital_id=hospital.id,
        status='completed'
    ).filter(EmergencyCase.created_at >= thirty_days_ago).count()
    
    # Stock info
    stocks = VenomStock.query.filter_by(hospital_id=hospital.id).all()
    
    return render_template(
        'hospital/analytics.html',
        hospital=hospital,
        total_cases=total_cases,
        accepted_cases=accepted_cases,
        completed_cases=completed_cases,
        stocks=stocks
    )


@hospital_bp.route('/notifications')
def notifications():
    """View hospital notifications"""
    hospital = get_current_hospital()
    if not hospital:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login'))
    
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(hospital_id=hospital.id).order_by(
        Notification.created_at.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template(
        'hospital/notifications.html',
        hospital=hospital,
        notifications=notifications
    )


@hospital_bp.route('/notification/<int:notif_id>/mark-read', methods=['POST'])
def mark_notification_read(notif_id):
    """Mark notification as read"""
    hospital = get_current_hospital()
    if not hospital:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    notification = Notification.query.get_or_404(notif_id)
    
    if notification.hospital_id != hospital.id:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})


@hospital_bp.route('/settings')
def settings():
    """Hospital settings"""
    hospital = get_current_hospital()
    if not hospital:
        flash('Please login first', 'danger')
        return redirect(url_for('auth.login'))
    
    return render_template('hospital/settings.html', hospital=hospital)


@hospital_bp.route('/settings/update', methods=['POST'])
def update_settings():
    """Update hospital settings"""
    hospital = get_current_hospital()
    if not hospital:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        beds = int(request.form.get('beds', 0))
        staff_count = int(request.form.get('staff_count', 0))
        
        hospital.phone = phone
        hospital.address = address
        hospital.beds = beds
        hospital.staff_count = staff_count
        hospital.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Settings updated successfully', 'success')
        return redirect(url_for('hospital.settings'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating settings: {str(e)}', 'danger')
        return redirect(url_for('hospital.settings'))
