from app.db import db
from sqlalchemy import Text, String, DECIMAL, Integer, Boolean, Date, Time, JSON
from datetime import datetime
import enum

class BookingStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Client Information
    client_name = db.Column(db.String(255), nullable=False)
    client_phone = db.Column(db.String(20), nullable=False)
    client_email = db.Column(db.String(255), nullable=False)
    
    # Booking Details
    service_type = db.Column(db.String(255), nullable=False)
    preferred_date = db.Column(db.Date, nullable=False)
    preferred_time = db.Column(db.Time, nullable=True)
    location = db.Column(db.Text, nullable=True)
    budget_range = db.Column(db.String(50), nullable=True)
    additional_notes = db.Column(db.Text, nullable=True)
    
    # Management
    status = db.Column(db.Enum(BookingStatus), nullable=False, default=BookingStatus.PENDING)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    internal_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    assigned_to_user = db.relationship('User', back_populates='bookings')

    def as_dict(self):
        return {
            "id": self.id,
            "client_name": self.client_name,
            "client_phone": self.client_phone,
            "client_email": self.client_email,
            "service_type": self.service_type,
            "preferred_date": self.preferred_date.isoformat(),
            "preferred_time": self.preferred_time.isoformat() if self.preferred_time else None,
            "location": self.location,
            "budget_range": self.budget_range,
            "additional_notes": self.additional_notes,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "internal_notes": self.internal_notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }