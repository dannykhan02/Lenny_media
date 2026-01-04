from app.db import db
from sqlalchemy import Text, String, DECIMAL, Integer, Boolean, Date, Time, JSON
from datetime import datetime
import enum

class CohortStatus(enum.Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Cohort(db.Model):
    __tablename__ = 'cohorts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)  # "January 2025 Intake"
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    max_students = db.Column(db.Integer, default=20, nullable=False)
    current_enrollment = db.Column(db.Integer, default=0, nullable=False)
    
    status = db.Column(db.Enum(CohortStatus), nullable=False, default=CohortStatus.UPCOMING)
    
    # Pricing
    course_fee = db.Column(DECIMAL(10, 2), nullable=False, default=15000.00)
    registration_fee = db.Column(DECIMAL(10, 2), default=2000.00, nullable=False)
    
    # Details``
    schedule_details = db.Column(db.Text, nullable=True)  # "Mon-Fri, 2pm-5pm"
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    instructor = db.relationship('User', back_populates='cohorts')
    enrollments = db.relationship('Enrollment', back_populates='cohort')

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "max_students": self.max_students,
            "current_enrollment": self.current_enrollment,
            "status": self.status.value,
            "course_fee": float(self.course_fee),
            "registration_fee": float(self.registration_fee),
            "schedule_details": self.schedule_details,
            "instructor_id": self.instructor_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }