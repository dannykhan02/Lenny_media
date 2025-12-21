from app.db import db
from sqlalchemy import Text, String, DECIMAL, Integer, Boolean, Date, Time, JSON
from datetime import datetime
import enum

class ServiceCategory(enum.Enum):
    PHOTOGRAPHY = "photography"
    VIDEOGRAPHY = "videography"

class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category = db.Column(db.Enum(ServiceCategory), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Pricing
    price_min = db.Column(DECIMAL(10, 2), nullable=True)
    price_max = db.Column(DECIMAL(10, 2), nullable=True)
    price_display = db.Column(db.String(100), nullable=True)  # "Ksh 40,000 – 150,000"
    
    # Features
    features = db.Column(JSON, nullable=True)  # ["4K Video", "Drone Coverage", "Same-day Edit"]
    
    # Display
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    icon_name = db.Column(db.String(50), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def as_dict(self):
        return {
            "id": self.id,
            "category": self.category.value,
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "price_min": float(self.price_min) if self.price_min else None,
            "price_max": float(self.price_max) if self.price_max else None,
            "price_display": self.price_display,
            "features": self.features,
            "is_active": self.is_active,
            "is_featured": self.is_featured,
            "display_order": self.display_order,
            "icon_name": self.icon_name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }