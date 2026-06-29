"""
Utility functions for authentication, location, and helpers
"""

import math
import requests
from functools import wraps
from flask import request, jsonify, session
from flask_login import current_user


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates using Haversine formula
    Returns distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def get_user_location():
    """Extract user location from request"""
    try:
        data = request.get_json() or request.form
        latitude = float(data.get('latitude', 0))
        longitude = float(data.get('longitude', 0))
        
        if latitude == 0 or longitude == 0:
            return None
        
        return {
            'latitude': latitude,
            'longitude': longitude,
            'district': data.get('district', ''),
            'village': data.get('village', '')
        }
    except (ValueError, TypeError):
        return None


def login_required_user(f):
    """Decorator to require user login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user type is 'user' (not hospital or admin)
        if hasattr(current_user, 'username') and not hasattr(current_user, 'is_verified'):
            return f(*args, **kwargs)
        
        return jsonify({'error': 'Access denied'}), 403
    
    return decorated_function


def login_required_hospital(f):
    """Decorator to require hospital login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'hospital_id' not in session:
            return jsonify({'error': 'Hospital authentication required'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def login_required_admin(f):
    """Decorator to require admin login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return jsonify({'error': 'Admin authentication required'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_nearby_hospitals(user_location, hospitals, radius_km=50):
    """
    Get hospitals within a certain radius
    
    Args:
        user_location: dict with latitude, longitude
        hospitals: list of Hospital objects
        radius_km: search radius in kilometers
    
    Returns:
        list of hospitals with distance, sorted by distance
    """
    nearby = []
    
    for hospital in hospitals:
        # Accept zero/negative coordinates but ensure they're not None
        if hospital.latitude is not None and hospital.longitude is not None:
            try:
                distance = calculate_distance(
                    float(user_location['latitude']),
                    float(user_location['longitude']),
                    float(hospital.latitude),
                    float(hospital.longitude)
                )
            except Exception:
                # Skip hospitals with invalid coordinate values
                continue
            
            if distance <= radius_km:
                nearby.append({
                    'hospital': hospital,
                    'distance': round(distance, 2)
                })
    
    # Sort by distance
    nearby.sort(key=lambda x: x['distance'])
    
    return nearby


def get_snake_venom_types():
    """Get common snake venom types in India"""
    return [
        'Common Krait',
        'Indian Cobra',
        'Russell\'s Viper',
        'Saw-scaled Viper',
        'King Cobra',
        'Spectacled Cobra',
        'Unknown'
    ]


def get_districts_list():
    """Get list of districts in Andhra Pradesh (common snake-bite areas)"""
    return [
        'Srikakulam', 'Vizianagaram', 'Visakhapatnam', 'East Godavari',
        'West Godavari', 'Krishna', 'Guntur', 'Prakasam',
        'Nellore', 'Chittoor', 'Kadapa', 'Anantapur'
    ]


def get_states_list():
    """Return list of Indian states and union territories (basic list)."""
    return [
        'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
        'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
        'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya',
        'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim',
        'Tamil Nadu', 'Telangana', 'Tripura', 'Uttarakhand', 'Uttar Pradesh',
        'West Bengal', 'Andaman and Nicobar Islands', 'Chandigarh',
        'Dadra and Nagar Haveli and Daman and Diu', 'Lakshadweep', 'Delhi',
        'Puducherry'
    ]


def translate_text(text, language='en'):
    """
    Simple translation for multi-language support
    English and Telugu support
    """
    translations = {
        'en': {
            'emergency': 'Emergency',
            'hospitals': 'Hospitals',
            'stock': 'Stock',
            'distance': 'Distance',
            'available': 'Available',
            'low_stock': 'Low Stock',
            'out_of_stock': 'Out of Stock'
        },
        'te': {
            'emergency': 'అత్యవసర',
            'hospitals': 'ఆసుపత్రులు',
            'stock': 'స్టాక్',
            'distance': 'దూరం',
            'available': 'అందుబాటులో',
            'low_stock': 'తక్కువ స్టాక్',
            'out_of_stock': 'స్టాక్ బయటకు'
        }
    }
    
    if language not in translations:
        language = 'en'
    
    return translations.get(language, translations['en'])


def send_sms_alert(phone_number, message):
    """
    Simulate SMS alert (can be replaced with Twilio integration)
    In production, use Twilio or similar service
    """
    # TODO: Integrate with Twilio or similar service
    print(f"[SMS] To: {phone_number}, Message: {message}")
    return True


def send_call_alert(phone_number, message):
    """
    Simulate call alert (could be replaced with voice/SIP integration)
    In production, use Twilio Voice or a similar provider.
    """
    # TODO: Integrate with Twilio Voice or similar service
    print(f"[CALL] To: {phone_number}, Message: {message}")
    return True


def send_email_alert(email, subject, body):
    """
    Simulate email alert (can be replaced with actual email service)
    In production, use Flask-Mail or similar
    """
    # TODO: Integrate with Flask-Mail
    # For now, just log it
    print(f"[EMAIL] To: {email}, Subject: {subject}, Body: {body}")
    return True
