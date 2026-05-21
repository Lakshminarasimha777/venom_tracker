# Venom_Tracker Setup Guide

Complete step-by-step guide to set up and run the Venom_Tracker application.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Database Setup](#database-setup)
5. [Running the Application](#running-the-application)
6. [Troubleshooting](#troubleshooting)
7. [Production Deployment](#production-deployment)

## System Requirements

### Minimum Requirements
- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment support
- 100MB disk space
- 512MB RAM

### Recommended
- Python 3.10+
- 1GB+ RAM
- SSD for better performance
- Linux/macOS/Windows 10+

### Browser Support
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Installation

### Step 1: Clone or Download the Project

```bash
# Using Git
git clone <repository-url>
cd venom_tracker

# Or download and extract the ZIP file
unzip venom_tracker.zip
cd venom_tracker
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv mln
mln\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv mln
source mln/bin/activate
```

You should see `(mln)` prefix in your terminal after activation.

### Step 3: Install Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

This will install:
- Flask and extensions
- SQLAlchemy for database ORM
- Python-dotenv for environment configuration
- All other required packages

### Step 4: Verify Installation

```bash
python -c "import flask; print(flask.__version__)"
```

Should print Flask version without errors.

## Configuration

### Step 1: Create Environment File

```bash
# Copy the example environment file
cp .env.example .env
```

### Step 2: Edit .env File

Open `.env` in your text editor and configure:

```ini
# Essential Settings
FLASK_ENV=development
DEBUG=True
SECRET_KEY=your-super-secret-key-change-this
JWT_SECRET_KEY=your-jwt-secret-key-change-this

# Database (SQLite is default)
DATABASE_URL=sqlite:///venom_tracker.db

# For PostgreSQL (optional)
# DATABASE_URL=postgresql://user:password@localhost:5432/venom_tracker

# For MySQL (optional)
# DATABASE_URL=mysql+pymysql://user:password@localhost:3306/venom_tracker

# Maps API (optional, for Google Maps)
GOOGLE_MAPS_API_KEY=your-api-key-here

# Email Settings (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### Security Notes
- **SECRET_KEY**: Generate a secure key
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- **JWT_SECRET_KEY**: Similar to above
- **Change defaults before production deployment**
- **Never commit .env file** (it's in .gitignore)

## Database Setup

### Step 1: Initialize Database

```bash
# Activate virtual environment first
# Windows: mln\Scripts\activate
# macOS/Linux: source mln/bin/activate

# Initialize database
flask init-db
```

This creates:
- `venom_tracker.db` file (if using SQLite)
- All required database tables

### Step 2: Populate Sample Data

```bash
flask seed-db
```

This creates:
- Admin user: `admin` / `admin123`
- Sample users and hospitals
- Pre-configured test data

### Step 3: Verify Database

```bash
# Check if database file exists
ls -la venom_tracker.db  # macOS/Linux
dir venom_tracker.db    # Windows
```

## Running the Application

### Development Mode (with hot reload)

```bash
python app.py
```

Visit `http://localhost:5000` in your browser

### Production Mode

```bash
python app.py --prod
```

Runs on `http://0.0.0.0:5000` (all network interfaces)

### Using Flask Command

```bash
flask run
```

### Specify Custom Port

```bash
# Using Flask
flask run --port 8000

# Using app.py
python app.py --port 8000
```

## First Login

### Access Points

1. **Main Site**: http://localhost:5000
2. **User Login**: http://localhost:5000/auth/login
3. **User Registration**: http://localhost:5000/auth/register
4. **Hospital Registration**: http://localhost:5000/auth/hospital-register

### Demo Credentials

| Role | Email/Username | Password |
|------|---|---|
| User | farmer1 | password123 |
| Hospital | city-hospital@example.com | hospital123 |
| Admin | admin | admin123 |

## Project Commands

### Database Commands

```bash
# Initialize database
flask init-db

# Seed sample data
flask seed-db

# Reset database
rm venom_tracker.db
flask init-db
flask seed-db
```

### Shell Commands

```bash
# Interactive Python shell with app context
flask shell

# Inside shell:
>>> from app.models import User
>>> users = User.query.all()
>>> print(users)
```

### Clean Up

```bash
# Remove all .pyc files
find . -type d -name __pycache__ -exec rm -r {} +

# Remove virtual environment (if needed)
rm -rf mln
```

## File Structure

After installation, your structure should look like:

```
venom_tracker/
├── app/                      # Application code
│   ├── __init__.py          # Flask app factory
│   ├── blueprints/          # Route blueprints
│   ├── models/              # Database models
│   └── utils/               # Helper functions
├── static/                  # Static files
│   ├── css/                 # Stylesheets
│   └── js/                  # JavaScript
├── templates/               # HTML templates
├── venom_tracker.db        # SQLite database (created after init-db)
├── app.py                  # Main application file
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── .gitignore              # Git ignore rules
└── README.md               # Documentation
```

## Troubleshooting

### Port Already in Use

```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :5000
kill -9 <PID>
```

### Module Not Found

```bash
# Verify virtual environment is activated
pip list  # Should show installed packages

# Reinstall requirements
pip install -r requirements.txt --upgrade
```

### Database Errors

```bash
# Reset database
rm venom_tracker.db

# Reinitialize
flask init-db
flask seed-db
```

### Permission Denied (macOS/Linux)

```bash
# Make scripts executable
chmod +x mln/bin/activate
chmod +x app.py
```

### CORS Issues

```python
# Add to config.py if needed
CORS_HEADERS = 'Content-Type'
SESSION_COOKIE_SAMESITE = 'Lax'
```

### 404 Errors After Registration

- Clear browser cache (Ctrl+Shift+Delete)
- Ensure virtual environment is activated
- Check Flask is running without errors

## Production Deployment

### Using Gunicorn

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Environment Configuration

Create `.env` for production:

```ini
FLASK_ENV=production
DEBUG=False
SECRET_KEY=<generate-secure-key>
JWT_SECRET_KEY=<generate-secure-key>
DATABASE_URL=postgresql://user:password@db:5432/venom_tracker
SESSION_COOKIE_SECURE=True
```

### Security Checklist

- [ ] Generate new SECRET_KEY and JWT_SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS/SSL
- [ ] Set strong passwords in .env
- [ ] Configure firewall
- [ ] Set up logging
- [ ] Enable CORS properly
- [ ] Regular database backups
- [ ] Monitor disk space

### Reverse Proxy Setup (Nginx)

```nginx
server {
    listen 80;
    server_name example.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Bootstrap 5 Docs](https://getbootstrap.com/)
- [Leaflet.js Docs](https://leafletjs.com/)

## Getting Help

If you encounter issues:

1. Check the README.md for general information
2. Review error messages in terminal output
3. Check Flask logs for detailed errors
4. Verify all dependencies are installed
5. Ensure .env file is properly configured
6. Try resetting the database

## Quick Start Summary

```bash
# 1. Activate virtual environment
source mln/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env

# 4. Initialize database
flask init-db
flask seed-db

# 5. Run application
python app.py

# 6. Open browser
# Visit http://localhost:5000
```

---

**Last Updated**: December 2024
**Version**: 1.0.0
