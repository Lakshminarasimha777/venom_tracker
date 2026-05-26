from app import create_app, db
from app.models import User, Hospital, Admin, VenomStock
import json

app = create_app()
app.app_context().push()

# Drop all tables and recreate
db.drop_all()
db.create_all()

# Create admin
if not Admin.query.filter_by(username='admin').first():
    admin = Admin(username='admin', email='admin@venom-tracker.com', is_super_admin=True)
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
        'license_number': 'LIC001',
        'venom_types': ['Common Krait', 'Indian Cobra', 'Russell\'s Viper']
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
        'license_number': 'LIC002',
        'venom_types': ['Common Krait', 'Indian Cobra']
    }
]

for hospital_data in sample_hospitals:
    venom_types = hospital_data.pop('venom_types')
    if not Hospital.query.filter_by(name=hospital_data['name']).first():
        hospital = Hospital(**hospital_data)
        hospital.set_password('hospital123')
        hospital.set_available_venom_types(venom_types)
        db.session.add(hospital)
        print(f'Hospital created: {hospital_data["name"]} with venom types: {venom_types}')
        
        # Add anti-venom stock
        for venom in venom_types:
            stock = VenomStock(venom_type=venom, quantity=10, minimum_threshold=3, updated_by=hospital_data['name'])
            hospital.venom_stocks.append(stock)

db.session.commit()
print('\nDatabase seeding completed!')
print('Default Credentials:')
print('  Admin: admin / admin123')
print('  Farmer: farmer1 / password123')
print('  Hospital: city-hospital@example.com / hospital123')
