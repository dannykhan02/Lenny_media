from app.db import db
from sqlalchemy import Text, String, DECIMAL, Integer, Boolean, Date, Time, JSON
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum

class UserRole(enum.Enum):
    ADMIN = "admin"
    PHOTOGRAPHER = "photographer" 
    STAFF = "staff"

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.STAFF)
    phone = db.Column(db.String(20), nullable=True)
    avatar_url = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    bookings = db.relationship('Booking', back_populates='assigned_to_user', foreign_keys='Booking.assigned_to', lazy=True)
    quote_requests = db.relationship('QuoteRequest', back_populates='assigned_to_user', foreign_keys='QuoteRequest.assigned_to', lazy=True)
    enrollments = db.relationship('Enrollment', back_populates='reviewed_by_user', foreign_keys='Enrollment.reviewed_by', lazy=True)
    portfolio_items = db.relationship('PortfolioItem', back_populates='instructor', foreign_keys='PortfolioItem.instructor_id', lazy=True)
    cohorts = db.relationship('Cohort', back_populates='instructor', foreign_keys='Cohort.instructor_id', lazy=True)
    email_logs = db.relationship('EmailLog', back_populates='user', foreign_keys='EmailLog.user_id', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_admin(self):
        return self.role == UserRole.ADMIN

    def is_photographer(self):
        return self.role == UserRole.PHOTOGRAPHER

    def is_staff(self):
        return self.role in [UserRole.ADMIN, UserRole.STAFF, UserRole.PHOTOGRAPHER]

    def as_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value,
            "phone": self.phone,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }