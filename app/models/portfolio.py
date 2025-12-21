from app.db import db
from sqlalchemy import Text, String, DECIMAL, Integer, Boolean, Date, Time, JSON
from datetime import datetime
import enum

class PortfolioCategory(enum.Enum):
    WEDDINGS = "Weddings"
    PORTRAITS = "Portraits"
    EVENTS = "Events"
    COMMERCIAL = "Commercial"

class PortfolioItem(db.Model):
    __tablename__ = 'portfolio_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.Enum(PortfolioCategory), nullable=False)
    
    # Media
    image_url = db.Column(db.Text, nullable=False)
    thumbnail_url = db.Column(db.Text, nullable=True)
    
    # Details
    description = db.Column(db.Text, nullable=True)
    client_name = db.Column(db.String(255), nullable=True)
    shoot_date = db.Column(db.Date, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    
    # Display
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    is_published = db.Column(db.Boolean, default=True, nullable=False)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    
    # SEO
    alt_text = db.Column(db.Text, nullable=True)
    tags = db.Column(JSON, nullable=True)  # ["outdoor", "golden-hour", "candid"]
    
    # Management
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    instructor = db.relationship('User', back_populates='portfolio_items')

    def as_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category.value,
            "image_url": self.image_url,
            "thumbnail_url": self.thumbnail_url,
            "description": self.description,
            "client_name": self.client_name,
            "shoot_date": self.shoot_date.isoformat() if self.shoot_date else None,
            "location": self.location,
            "is_featured": self.is_featured,
            "is_published": self.is_published,
            "display_order": self.display_order,
            "alt_text": self.alt_text,
            "tags": self.tags,
            "instructor_id": self.instructor_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }