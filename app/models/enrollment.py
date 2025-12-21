from app.db import db
from sqlalchemy import Text, String, DECIMAL, Integer, Boolean, Date, Time, JSON
from datetime import datetime
import enum

class EnrollmentStatus(enum.Enum):
    PENDING = "pending"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ENROLLED = "enrolled"
    COMPLETED = "completed"

class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Student Information
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    
    # Background
    education_occupation = db.Column(db.Text, nullable=True)
    experience_level = db.Column(db.String(50), nullable=True)
    has_own_camera = db.Column(db.Boolean, default=False, nullable=False)
    learning_goals = db.Column(db.Text, nullable=True)
    
    # Enrollment
    preferred_intake = db.Column(db.String(50), nullable=True)
    cohort_id = db.Column(db.Integer, db.ForeignKey('cohorts.id'), nullable=True)
    status = db.Column(db.Enum(EnrollmentStatus), nullable=False, default=EnrollmentStatus.PENDING)
    
    # Payment
    registration_fee_paid = db.Column(db.Boolean, default=False, nullable=False)
    payment_reference = db.Column(db.String(100), nullable=True)
    
    # Management
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    reviewed_by_user = db.relationship('User', back_populates='enrollments')
    cohort = db.relationship('Cohort', back_populates='enrollments')

    def as_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "age": self.age,
            "education_occupation": self.education_occupation,
            "experience_level": self.experience_level,
            "has_own_camera": self.has_own_camera,
            "learning_goals": self.learning_goals,
            "preferred_intake": self.preferred_intake,
            "cohort_id": self.cohort_id,
            "status": self.status.value,
            "registration_fee_paid": self.registration_fee_paid,
            "payment_reference": self.payment_reference,
            "reviewed_by": self.reviewed_by,
            "admin_notes": self.admin_notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }