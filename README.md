# Venom_Tracker - Emergency Anti-Venom Network

A full-stack web application that helps farmers and snake-bite victims quickly find nearby hospitals with anti-venom stock availability.

## 🎯 Project Overview

Venom_Tracker is a life-saving emergency response system designed to bridge the gap between snake-bite patients and medical facilities equipped with anti-venom. The system provides:

- **Real-time hospital location and availability tracking**
- **Emergency SOS alerts to nearby hospitals**
- **Anti-venom stock management and monitoring**
- **Emergency case tracking and management**
- **Analytics and statistics dashboard**
- **Multi-role access (Users, Hospitals, Admins)**

## ✨ Key Features

### User Dashboard
- GPS-based hospital location detection
- Find nearby hospitals with anti-venom availability
- Sort hospitals by distance
- Emergency SOS button to alert nearby hospitals
- Track emergency cases in real-time
- View notifications from hospitals
- First-aid guidance and information
- Mobile-responsive dark mode support

### Hospital Dashboard
- Update anti-venom stock in real-time
- Accept/reject emergency cases
- View incoming emergency alerts
- Patient case management
- Analytics: cases per day, stock levels, emergency requests
- Notification system for new cases

### Admin Dashboard
- Manage all users and hospitals
- Verify new hospital registrations
- Block fake hospitals/users
- View all emergency cases
- Advanced analytics:
  - Snake-bite cases per district
  - Monthly statistics
  - Stock availability reports
- System-wide monitoring

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask 3.0
- **Database**: SQLite/MySQL/PostgreSQL (SQLAlchemy ORM)
- **Authentication**: Flask-Login, Session-based
- **API**: RESTful endpoints with JSON responses

### Frontend
- **HTML5** with Jinja2 templates
- **CSS3** with Bootstrap 5
- **JavaScript** (Vanilla JS with ES6+)
- **Maps**: Leaflet.js for interactive maps
- **Charts**: Chart.js for analytics

### Additional Libraries
- **python-dotenv**: Environment configuration
- **Werkzeug**: Password hashing and utilities
- **Blinker**: Signal support for Flask

## 📋 Database Schema

### Tables
1. **users** - Patient/Farmer accounts
2. **hospitals** - Hospital information and credentials
3. **admins** - Administrator accounts
4. **venom_stock** - Anti-venom inventory tracking
5. **emergency_cases** - Emergency case records
6. **notifications** - System notifications
7. **system_logs** - Audit trail

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Virtual environment (recommended)
- Git

### Installation Steps

#### 1. Clone the Repository
```bash
cd Desktop
git clone <repository-url>
cd venom_tracker
```

#### 2. Create Virtual Environment
```bash
# Windows
python -m venv mln
mln\Scripts\activate

# macOS/Linux
python3 -m venv mln
source mln/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
# At minimum, set SECRET_KEY and JWT_SECRET_KEY
# For production or Render deployment:
# FLASK_ENV=production
# DEBUG=False
# Optionally use DATABASE_URL for Postgres when ready
```

#### 5. Initialize Database
```bash
# Create database tables
python app.py
flask db init
flask db migrate
flask db upgrade

# Or use the built-in command
flask init-db
```

> Note: If you deploy to Render, set the environment variables in the Render dashboard instead of relying on a local `.env` file.

#### 6. Seed Sample Data
```bash
flask seed-db
```

This creates:
- Admin account: `admin` / `admin123`
- Sample users and hospitals with pre-configured data

#### 7. Run the Application
```bash
# Development mode (with hot reload)
python app.py

# Production mode
python app.py --prod
```

The application will be available at `http://localhost:5000`

## 📚 Project Structure

```
venom_tracker/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models/
│   │   └── __init__.py          # SQLAlchemy models
│   ├── blueprints/
│   │   ├── auth.py              # Authentication routes
│   │   ├── user.py              # User dashboard routes
│   │   ├── hospital.py          # Hospital dashboard routes
│   │   ├── admin.py             # Admin dashboard routes
│   │   └── api.py               # REST API endpoints
│   └── utils/
│       └── __init__.py          # Helper functions
├── static/
│   ├── css/
│   │   └── style.css            # Custom styles
│   └── js/
│       └── main.js              # Client-side JavaScript
├── templates/
│   ├── base.html                # Base template
│   ├── index.html               # Home page
│   ├── about.html               # About page
│   ├── auth/
│   │   ├── login.html           # Login page
│   │   ├── register.html        # User registration
│   │   └── register_hospital.html# Hospital registration
│   ├── user/                    # User dashboard templates
│   ├── hospital/                # Hospital dashboard templates
│   ├── admin/                   # Admin dashboard templates
│   └── errors/                  # Error pages
├── app.py                       # Main entry point
├── config.py                    # Configuration settings
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
└── README.md                    # This file
```

## 🔑 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/hospital-register` - Hospital registration
- `GET /auth/logout` - Logout

### Hospitals API
- `GET /api/v1/hospitals` - List all hospitals
- `POST /api/v1/hospitals/nearby` - Find nearby hospitals
- `GET /api/v1/hospitals/<id>` - Get hospital details
- `GET /api/v1/stock/<hospital_id>` - Get hospital stock

### Emergency Cases API
- `POST /api/v1/emergency-cases` - Create emergency case
- `GET /api/v1/emergency-cases/<id>` - Get case details
- `GET /api/v1/emergency-cases/<id>/status` - Get case status

### Analytics API
- `GET /api/v1/analytics/district/<district>` - District statistics
- `GET /api/v1/analytics/snake-types` - Snake-bite statistics
- `GET /api/v1/health` - Health check

## 🔐 Security Features

- **Password Hashing**: Werkzeug security for password storage
- **Session Management**: Secure session cookies
- **CSRF Protection**: Flask built-in protection
- **Input Validation**: Server-side validation for all inputs
- **SQL Injection Prevention**: SQLAlchemy parameterized queries
- **Role-based Access Control**: Different permissions for users, hospitals, admins

## 📱 Mobile Responsiveness

The application is fully responsive and works seamlessly on:
- Desktop browsers (1920px+)
- Tablets (768px - 1024px)
- Mobile devices (320px - 767px)

Bootstrap 5 grid system ensures optimal layout on all devices.

## 🗺️ Map Integration

The application uses **Leaflet.js** for interactive maps:
- Real-time location detection using browser GPS
- Hospital markers with information windows
- Distance calculation using Haversine formula
- Route directions to hospitals

## 📊 Database Models

### User Model
- Basic user information
- Location tracking (latitude, longitude)
- Language preference (English, Telugu)
- Theme preference (light, dark)
- Password hashing

### Hospital Model
- Hospital details and location
- Verification status
- Anti-venom stock management
- Contact information
- Analytics tracking

### Emergency Case Model
- Case details (snake type, severity, location)
- Hospital assignment
- Status tracking (pending, accepted, completed)
- Medical notes and observations

## 🌐 Multi-Language Support

Currently supports:
- **English** (en)
- **Telugu** (te)

Easy to extend to other languages through the translation system.

## 📈 Analytics Features

### User Analytics
- Emergency cases per user
- Case outcomes
- Response times

### Hospital Analytics
- Cases handled per day/month/year
- Stock consumption rates
- Average response times
- Case success rates

### System Analytics
- District-wise statistics
- Snake-bite trends
- Stock availability by region
- Emergency response metrics

## 🔄 Background Tasks

The application can be extended with Celery for background tasks:
- SMS/Email notifications
- Scheduled stock updates
- Report generation
- Data cleanup

## 🚨 Error Handling

Comprehensive error handling for:
- 404 - Page Not Found
- 403 - Access Forbidden
- 500 - Server Error
- Form validation errors
- Database errors
- API errors

## 📝 Demo Credentials

After running `flask seed-db`:

| Role | Username | Password |
|------|----------|----------|
| User | farmer1 | password123 |
| Hospital | city-hospital@example.com | hospital123 |
| Admin | admin | admin123 |

## 🔧 Configuration Options

### Database
- `SQLALCHEMY_DATABASE_URI` - Database connection string
- `SQLALCHEMY_TRACK_MODIFICATIONS` - Track model modifications

### Security
- `SECRET_KEY` - Flask session secret
- `JWT_SECRET_KEY` - JWT token secret
- `SESSION_COOKIE_SECURE` - HTTPS only cookies
- `SESSION_COOKIE_HTTPONLY` - JavaScript cookie access

### Features
- `MAX_SEARCH_RADIUS_KM` - Maximum hospital search radius
- `ITEMS_PER_PAGE` - Pagination items per page
- `MAX_CONTENT_LENGTH` - Maximum file upload size

## 🐛 Troubleshooting

### Database Issues
```bash
# Reset database
rm venom_tracker.db
flask init-db
flask seed-db
```

### Port Already in Use
```bash
# Change port in app.py or use environment variable
python app.py --port 5001
```

### Missing Dependencies
```bash
pip install -r requirements.txt --upgrade
```

## 📝 Logging

Logs are output to console in development mode. For production:
- Configure file-based logging in `app.py`
- Set log level via environment variables
- Monitor logs for errors and warnings

## 🎯 Future Enhancements

- [ ] SMS integration for emergency alerts
- [ ] Email notifications
- [ ] Push notifications
- [ ] Video call integration for telemedicine
- [ ] AI-powered first-aid guidance
- [ ] Machine learning for case prediction
- [ ] Mobile app (iOS/Android)
- [ ] Advanced analytics dashboard
- [ ] Integration with government health systems

## 📞 Emergency Helpline

**National Poison Control Helpline (India)**
- **Number**: 1800-11-6117
- Available 24/7 for emergency assistance

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 👥 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## ⚠️ Disclaimer

This application is designed for emergency response purposes. While we strive to provide accurate information, always verify hospital information and anti-venom availability directly with the hospital. In case of life-threatening emergency, call emergency services immediately.

## 📧 Support

For support, email: support@venom-tracker.com

## 🙏 Acknowledgments

- Bootstrap team for the excellent UI framework
- Leaflet.js for interactive maps
- OpenStreetMap contributors
- Chart.js for data visualization

---

**Last Updated**: December 2024
**Version**: 1.0.0
**Status**: Production Ready
