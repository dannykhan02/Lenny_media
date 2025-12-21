from app.db import db
from sqlalchemy import Text, String, DECIMAL, Integer, Boolean, Date, Time, JSON
from datetime import datetime
import enum

class QuoteStatus(enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class QuoteRequest(db.Model):
    __tablename__ = 'quote_requests'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Client Information
    client_name = db.Column(db.String(255), nullable=False)
    client_email = db.Column(db.String(255), nullable=False)
    client_phone = db.Column(db.String(20), nullable=False)
    company_name = db.Column(db.String(255), nullable=True)
    
    # Quote Details
    selected_services = db.Column(JSON, nullable=False)  # Array of service IDs
    event_date = db.Column(db.Date, nullable=True)
    event_location = db.Column(db.Text, nullable=True)
    budget_range = db.Column(db.String(50), nullable=True)
    project_description = db.Column(db.Text, nullable=True)
    referral_source = db.Column(db.String(50), nullable=True)
    
    # Quote Response
    status = db.Column(db.Enum(QuoteStatus), nullable=False, default=QuoteStatus.PENDING)
    quoted_amount = db.Column(DECIMAL(10, 2), nullable=True)
    quote_details = db.Column(db.Text, nullable=True)
    quote_sent_at = db.Column(db.DateTime, nullable=True)
    valid_until = db.Column(db.Date, nullable=True)
    
    # Management
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    assigned_to_user = db.relationship('User', back_populates='quote_requests')

    def as_dict(self):
        return {
            "id": self.id,
            "client_name": self.client_name,
            "client_email": self.client_email,
            "client_phone": self.client_phone,
            "company_name": self.company_name,
            "selected_services": self.selected_services,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "event_location": self.event_location,
            "budget_range": self.budget_range,
            "project_description": self.project_description,
            "referral_source": self.referral_source,
            "status": self.status.value,
            "quoted_amount": float(self.quoted_amount) if self.quoted_amount else None,
            "quote_details": self.quote_details,
            "quote_sent_at": self.quote_sent_at.isoformat() if self.quote_sent_at else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }