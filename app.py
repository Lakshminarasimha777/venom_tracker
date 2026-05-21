"""
Venom_Tracker Application
Main entry point for the application

Usage:
    python app.py          # Run in development mode
    python app.py --prod   # Run in production mode
"""

import os
import sys
from dotenv import load_dotenv
from app import create_app, db
from app.models import User, Hospital, Admin, EmergencyCase, VenomStock, Notification

# Load environment variables from .env file
load_dotenv()

# Create Flask app
app = create_app(os.getenv('FLASK_ENV', 'development'))


@app.shell_context_processor
def make_shell_context():
    """Context for flask shell"""
    return {
        'db': db,
        'User': User,
        'Hospital': Hospital,
        'Admin': Admin,
        'EmergencyCase': EmergencyCase,
        'VenomStock': VenomStock,
        'Notification': Notification
    }


@app.cli.command()
def init_db():
    """Initialize the database"""
    db.create_all()
    print('Database initialized!')


@app.cli.command()
def seed_db():
    """Seed the database with sample data"""
    try:
        # Create admin
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(
                username='admin',
                email='admin@venom-tracker.com',
                is_super_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print('Admin created: admin / admin123')
        
        # Create sample users
        sample_users = [
            {'username': 'farmer1', 'email': 'farmer1@example.com', 'phone': '9876543210', 'district': 'Visakhapatnam'},
            {'username': 'farmer2', 'email': 'farmer2@example.com', 'phone': '9876543211', 'district': 'Vizianagaram'},
        ]
        
        for user_data in sample_users:
            if not User.query.filter_by(username=user_data['username']).first():
                user = User(**user_data)
                user.set_password('password123')
                db.session.add(user)
                print(f'User created: {user_data["username"]} / password123')
        
        # Create sample hospitals
        sample_hospitals = [
            {
                'name': 'City Medical Hospital',
                'email': 'city-hospital@example.com',
                'phone': '08923123456',
                'address': '123 Main Street',
                'district': 'Visakhapatnam',
                'state': 'Andhra Pradesh',
                'pincode': '530001',
                'latitude': 17.6869,
                'longitude': 83.2185,
                'is_verified': True,
                'registration_number': 'REG001',
                'license_number': 'LIC001'
            },
            {
                'name': 'District Government Hospital',
                'email': 'district-hospital@example.com',
                'phone': '08927987654',
                'address': '456 Hospital Road',
                'district': 'Visakhapatnam',
                'state': 'Andhra Pradesh',
                'pincode': '530003',
                'latitude': 17.7150,
                'longitude': 83.3000,
                'is_verified': True,
                'registration_number': 'REG002',
                'license_number': 'LIC002'
            },
            {
                'name': 'Rural Health Center',
                'email': 'rural-health@example.com',
                'phone': '08914567890',
                'address': '789 Village Road',
                'district': 'Vizianagaram',
                'state': 'Andhra Pradesh',
                'pincode': '535001',
                'latitude': 18.1213,
                'longitude': 83.4277,
                'is_verified': True,
                'registration_number': 'REG003',
                'license_number': 'LIC003'
            }
        ]
        
        for hospital_data in sample_hospitals:
            if not Hospital.query.filter_by(name=hospital_data['name']).first():
                hospital = Hospital(**hospital_data)
                hospital.set_password('hospital123')
                db.session.add(hospital)
                print(f'Hospital created: {hospital_data["name"]}')
                
                # Add anti-venom stock for hospitals
                venom_types = ['Common Krait', 'Indian Cobra', 'Russell\'s Viper', 'Saw-scaled Viper']
                for venom in venom_types:
                    stock = VenomStock(
                        venom_type=venom,
                        quantity=10,
                        minimum_threshold=3,
                        updated_by=hospital_data['name']
                    )
                    hospital.venom_stocks.append(stock)
        
        db.session.commit()
        print('\nDatabase seeding completed!')
        print('\nDefault Credentials:')
        print('  Admin: admin / admin123')
        print('  Farmer: farmer1 / password123')
        print('  Hospital: city-hospital@example.com / hospital123')
    
    except Exception as e:
        db.session.rollback()
        print(f'Error seeding database: {str(e)}')
        sys.exit(1)


if __name__ == '__main__':
    # Get environment from command line
    if len(sys.argv) > 1 and sys.argv[1] == '--prod':
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        # Development mode
        app.run(host='127.0.0.1', port=5000, debug=True)
