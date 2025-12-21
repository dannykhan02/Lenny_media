from app.db import db
from sqlalchemy import Text, String, DECIMAL, Integer, Boolean, Date, Time, JSON
from datetime import datetime
import enum

class BusinessInfo(db.Model):
    __tablename__ = 'business_info'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Contact
    business_name = db.Column(db.String(255), nullable=False, default='Lenny Media Kenya')
    address = db.Column(db.Text, nullable=False)
    phone_primary = db.Column(db.String(20), nullable=False)
    phone_secondary = db.Column(db.String(20), nullable=True)
    email_primary = db.Column(db.String(255), nullable=False)
    email_support = db.Column(db.String(255), nullable=True)
    
    # Hours
    hours_of_operation = db.Column(JSON, nullable=False)
    # Example: {"monday": "8:00 AM - 6:00 PM", "tuesday": "8:00 AM - 6:00 PM", ...}
    
    # Social Media
    social_media = db.Column(JSON, nullable=True)
    # Example: {"instagram": "https://instagram.com/lennymedia", "facebook": "https://facebook.com/lennymedia"}
    
    # Map
    google_maps_embed_url = db.Column(db.Text, nullable=True)
    latitude = db.Column(DECIMAL(10, 8), nullable=True)
    longitude = db.Column(DECIMAL(11, 8), nullable=True)
    
    # Only one active record
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def as_dict(self):
        return {
            "id": self.id,
            "business_name": self.business_name,
            "address": self.address,
            "phone_primary": self.phone_primary,
            "phone_secondary": self.phone_secondary,
            "email_primary": self.email_primary,
            "email_support": self.email_support,
            "hours_of_operation": self.hours_of_operation,
            "social_media": self.social_media,
            "google_maps_embed_url": self.google_maps_embed_url,
            "latitude": float(self.latitude) if self.latitude else None,
            "longitude": float(self.longitude) if self.longitude else None,
            "is_active": self.is_active,
            "updated_at": self.updated_at.isoformat()
        }