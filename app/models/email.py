from app.db import db
from sqlalchemy import Text, String, DECIMAL, Integer, Boolean, Date, Time, JSON
from datetime import datetime
import enum

class EmailLogStatus(enum.Enum):
    SENT = "sent"
    FAILED = "failed"
    PENDING = "pending"

class EmailLog(db.Model):
    __tablename__ = 'email_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipient_email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255), nullable=True)
    template_name = db.Column(db.String(100), nullable=True)
    status = db.Column(db.Enum(EmailLogStatus), nullable=False, default=EmailLogStatus.PENDING)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    related_booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=True)
    related_quote_id = db.Column(db.Integer, db.ForeignKey('quote_requests.id'), nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='email_logs')

    def as_dict(self):
        return {
            "id": self.id,
            "recipient_email": self.recipient_email,
            "subject": self.subject,
            "template_name": self.template_name,
            "status": self.status.value,
            "user_id": self.user_id,
            "related_booking_id": self.related_booking_id,
            "related_quote_id": self.related_quote_id,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat()
        }