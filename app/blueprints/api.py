"""
REST API blueprint for Venom_Tracker
Provides endpoints for mobile apps and external integrations
"""

from flask import Blueprint, request, jsonify
from app.models import db, Hospital, VenomStock, EmergencyCase, User
from app.utils import calculate_distance, get_nearby_hospitals
from sqlalchemy import func
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


# ============== Hospital Endpoints ==============

@api_bp.route('/hospitals', methods=['GET'])
def get_hospitals():
    """Get all verified hospitals"""
    try:
        page = request.args.get('page', 1, type=int)
        district = request.args.get('district', '')
        
        query = Hospital.query.filter_by(is_verified=True, is_active=True)
        
        if district:
            query = query.filter_by(district=district)
        
        hospitals = query.paginate(page=page, per_page=20)
        
        return jsonify({
            'success': True,
            'data': [{
                'id': h.id,
                'name': h.name,
                'phone': h.phone,
                'address': h.address,
                'district': h.district,
                'latitude': h.latitude,
                'longitude': h.longitude,
                'overall_stock_status': h.overall_stock_status,
                'beds': h.beds
            } for h in hospitals.items],
            'total': hospitals.total,
            'pages': hospitals.pages,
            'current_page': page
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@api_bp.route('/hospitals/nearby', methods=['POST'])
def get_nearby_hospitals_api():
    """Get hospitals nearby user location"""
    try:
        data = request.get_json()
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        radius = float(data.get('radius', 50))
        
        if not latitude or not longitude:
            return jsonify({'success': False, 'error': 'Invalid location'}), 400
        
        user_location = {'latitude': latitude, 'longitude': longitude}
        hospitals = Hospital.query.filter_by(is_verified=True, is_active=True).all()
        
        nearby = get_nearby_hospitals(user_location, hospitals, radius)
        
        result = []
        for item in nearby:
            hospital = item['hospital']
            distance = item['distance']
            
            # Get stock info
            stocks = VenomStock.query.filter_by(hospital_id=hospital.id).all()
            total_stock = sum(s.quantity for s in stocks)
            
            result.append({
                'id': hospital.id,
                'name': hospital.name,
                'phone': hospital.phone,
                'address': hospital.address,
                'district': hospital.district,
                'latitude': hospital.latitude,
                'longitude': hospital.longitude,
                'distance_km': distance,
                'total_stock': total_stock,
                'overall_status': hospital.overall_stock_status,
                'beds': hospital.beds,
                'staff': hospital.staff_count
            })
        
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@api_bp.route('/hospitals/<int:hospital_id>', methods=['GET'])
def get_hospital_detail(hospital_id):
    """Get hospital details"""
    try:
        hospital = Hospital.query.get_or_404(hospital_id)
        
        # Get stocks
        stocks = VenomStock.query.filter_by(hospital_id=hospital.id).all()
        stock_data = [{
            'id': s.id,
            'venom_type': s.venom_type,
            'quantity': s.quantity,
            'status': s.get_status()
        } for s in stocks]
        
        return jsonify({
            'success': True,
            'data': {
                'id': hospital.id,
                'name': hospital.name,
                'email': hospital.email,
                'phone': hospital.phone,
                'address': hospital.address,
                'district': hospital.district,
                'state': hospital.state,
                'pincode': hospital.pincode,
                'latitude': hospital.latitude,
                'longitude': hospital.longitude,
                'beds': hospital.beds,
                'staff': hospital.staff_count,
                'overall_status': hospital.overall_stock_status,
                'is_verified': hospital.is_verified,
                'stocks': stock_data,
                'total_stock': sum(s.quantity for s in stocks)
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ============== Stock Endpoints ==============

@api_bp.route('/stock/<int:hospital_id>', methods=['GET'])
def get_hospital_stock(hospital_id):
    """Get hospital stock information"""
    try:
        hospital = Hospital.query.get_or_404(hospital_id)
        stocks = VenomStock.query.filter_by(hospital_id=hospital.id).all()
        
        return jsonify({
            'success': True,
            'hospital': hospital.name,
            'data': [{
                'id': s.id,
                'venom_type': s.venom_type,
                'quantity': s.quantity,
                'minimum_threshold': s.minimum_threshold,
                'status': s.get_status(),
                'last_updated': s.last_updated.isoformat()
            } for s in stocks],
            'total_stock': sum(s.quantity for s in stocks)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ============== Emergency Case Endpoints ==============

@api_bp.route('/emergency-cases', methods=['POST'])
def create_emergency_case():
    """Create emergency case (for mobile apps)"""
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        latitude = float(data.get('latitude', 0))
        longitude = float(data.get('longitude', 0))
        snake_type = data.get('snake_type', 'Unknown')
        severity = data.get('severity', 'moderate')
        location = data.get('location', '')
        description = data.get('description', '')
        
        if not user_id or latitude == 0 or longitude == 0:
            return jsonify({'success': False, 'error': 'Invalid data'}), 400
        
        # Verify user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Create emergency case
        emergency_case = EmergencyCase(
            user_id=user_id,
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
        
        # Find nearby hospitals
        hospitals = Hospital.query.filter_by(is_verified=True, is_active=True).all()
        user_location = {'latitude': latitude, 'longitude': longitude}
        nearby = get_nearby_hospitals(user_location, hospitals, 10)[:5]
        
        # Assign to first 5 hospitals
        for item in nearby:
            hospital = item['hospital']
            new_case = EmergencyCase(
                user_id=user_id,
                hospital_id=hospital.id,
                snake_type=snake_type,
                location=location,
                latitude=latitude,
                longitude=longitude,
                severity=severity,
                description=description,
                status='pending'
            )
            db.session.add(new_case)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Emergency case created',
            'case_id': emergency_case.id,
            'hospitals_notified': len(nearby)
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@api_bp.route('/emergency-cases/<int:case_id>', methods=['GET'])
def get_emergency_case(case_id):
    """Get emergency case details"""
    try:
        case = EmergencyCase.query.get_or_404(case_id)
        
        hospital_info = None
        if case.hospital:
            hospital_info = {
                'id': case.hospital.id,
                'name': case.hospital.name,
                'phone': case.hospital.phone,
                'address': case.hospital.address
            }
        
        return jsonify({
            'success': True,
            'data': {
                'id': case.id,
                'snake_type': case.snake_type,
                'location': case.location,
                'latitude': case.latitude,
                'longitude': case.longitude,
                'severity': case.severity,
                'status': case.status,
                'description': case.description,
                'medical_notes': case.medical_notes,
                'created_at': case.created_at.isoformat(),
                'updated_at': case.updated_at.isoformat(),
                'hospital': hospital_info
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@api_bp.route('/emergency-cases/<int:case_id>/status', methods=['GET'])
def get_emergency_case_status(case_id):
    """Get emergency case status"""
    try:
        case = EmergencyCase.query.get_or_404(case_id)
        
        return jsonify({
            'success': True,
            'case_id': case.id,
            'status': case.status,
            'hospital': case.hospital.name if case.hospital else None,
            'hospital_phone': case.hospital.phone if case.hospital else None,
            'updated_at': case.updated_at.isoformat()
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ============== Analytics Endpoints ==============

@api_bp.route('/analytics/district/<district>', methods=['GET'])
def get_district_analytics(district):
    """Get district statistics"""
    try:
        # Get hospitals in district
        hospitals = Hospital.query.filter_by(district=district, is_verified=True).all()
        hospital_ids = [h.id for h in hospitals]
        
        # Get cases in district in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        cases = EmergencyCase.query.filter(
            EmergencyCase.created_at >= thirty_days_ago,
            EmergencyCase.hospital_id.in_(hospital_ids) if hospital_ids else False
        ).all()
        
        # Get total stock
        total_stock = db.session.query(func.sum(VenomStock.quantity)).filter(
            VenomStock.hospital_id.in_(hospital_ids) if hospital_ids else False
        ).scalar() or 0
        
        # Cases by status
        case_status = {}
        for case in cases:
            status = case.status
            case_status[status] = case_status.get(status, 0) + 1
        
        return jsonify({
            'success': True,
            'district': district,
            'data': {
                'total_hospitals': len(hospitals),
                'total_cases_30days': len(cases),
                'total_stock': total_stock,
                'cases_by_status': case_status,
                'hospitals': [{'name': h.name, 'phone': h.phone} for h in hospitals]
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@api_bp.route('/analytics/snake-types', methods=['GET'])
def get_snake_type_analytics():
    """Get statistics by snake type"""
    try:
        # Get cases in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        snake_stats = db.session.query(
            EmergencyCase.snake_type,
            func.count(EmergencyCase.id)
        ).filter(
            EmergencyCase.created_at >= thirty_days_ago
        ).group_by(EmergencyCase.snake_type).all()
        
        return jsonify({
            'success': True,
            'data': [{
                'snake_type': s[0] or 'Unknown',
                'cases': s[1]
            } for s in snake_stats]
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ============== Health Check ==============

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'Venom_Tracker API is running',
        'timestamp': datetime.utcnow().isoformat()
    })
