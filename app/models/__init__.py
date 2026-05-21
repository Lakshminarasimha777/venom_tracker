"""
Database models for Venom_Tracker application
Uses SQLAlchemy ORM for database abstraction
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for patients/farmers"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    
    # Location info
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    district = db.Column(db.String(100), nullable=True)
    village = db.Column(db.String(100), nullable=True)
    
    # Account info
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    language_preference = db.Column(db.String(10), default='en')  # en, te (Telugu)
    theme = db.Column(db.String(10), default='light')  # light, dark
    
    # Relationships
    emergency_cases = db.relationship('EmergencyCase', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Hospital(db.Model):
    """Hospital model"""
    __tablename__ = 'hospitals'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    
    # Location
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.Text, nullable=False)
    district = db.Column(db.String(100), nullable=False, index=True)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    
    # Hospital details
    registration_number = db.Column(db.String(100), nullable=True)
    license_number = db.Column(db.String(100), nullable=True)
    beds = db.Column(db.Integer, default=0)
    staff_count = db.Column(db.Integer, default=0)
    
    # Status
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    overall_stock_status = db.Column(db.String(20), default='good')  # good, low, critical
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    venom_stocks = db.relationship('VenomStock', backref='hospital', lazy='dynamic', cascade='all, delete-orphan')
    emergency_cases = db.relationship('EmergencyCase', backref='hospital', lazy='dynamic')
    notifications = db.relationship('Notification', backref='hospital', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_total_stock(self):
        """Get total anti-venom stock"""
        return db.session.query(db.func.sum(VenomStock.quantity)).filter(
            VenomStock.hospital_id == self.id
        ).scalar() or 0
    
    def __repr__(self):
        return f'<Hospital {self.name}>'


class VenomStock(db.Model):
    """Anti-venom stock management"""
    __tablename__ = 'venom_stock'
    
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False, index=True)
    
    venom_type = db.Column(db.String(100), nullable=False)  # Common krait, Cobra, Viper, etc.
    quantity = db.Column(db.Integer, default=0)
    minimum_threshold = db.Column(db.Integer, default=5)
    
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(100), nullable=True)
    
    def get_status(self):
        """Get stock status"""
        if self.quantity == 0:
            return 'out_of_stock'
        elif self.quantity <= self.minimum_threshold:
            return 'low_stock'
        else:
            return 'available'
    
    def __repr__(self):
        return f'<VenomStock {self.venom_type}>'


class EmergencyCase(db.Model):
    """Emergency case tracking"""
    __tablename__ = 'emergency_cases'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=True, index=True)
    
    # Case details
    snake_type = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    severity = db.Column(db.String(20), default='moderate')  # mild, moderate, severe
    
    # Status
    status = db.Column(db.String(50), default='pending')  # pending, accepted, rejected, completed
    hospital_response_time = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Notes
    description = db.Column(db.Text, nullable=True)
    medical_notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    notifications = db.relationship('Notification', backref='emergency_case', lazy='dynamic')
    
    def __repr__(self):
        return f'<EmergencyCase {self.id}>'


class Admin(db.Model):
    """Admin user model"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Permissions
    is_super_admin = db.Column(db.Boolean, default=False)
    permissions = db.Column(db.JSON, default={})  # Store permissions as JSON
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Admin {self.username}>'


class Notification(db.Model):
    """Notification system"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=True)
    emergency_case_id = db.Column(db.Integer, db.ForeignKey('emergency_cases.id'), nullable=True)
    
    type = db.Column(db.String(50), nullable=False)  # emergency_alert, stock_update, case_update, etc.
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    is_sent_via_sms = db.Column(db.Boolean, default=False)
    is_sent_via_email = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Notification {self.type}>'


class SystemLog(db.Model):
    """System activity logging"""
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    actor_type = db.Column(db.String(50), nullable=False)  # user, hospital, admin
    actor_id = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<SystemLog {self.action}>'
