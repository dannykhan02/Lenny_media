import json
from flask import request, jsonify, current_app
from flask_restful import Resource
from datetime import datetime, date, time, timedelta, timezone
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy import or_, and_

from ..models import User, UserRole
from ..models.booking import Booking, BookingStatus
from .. import db
from ..services import (
    send_email,
    booking_confirmation_template,
    admin_booking_alert_template,
    booking_status_update_template
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BookingResource(Resource):
    """Resource for handling individual bookings and booking creation."""
    
    def post(self):
        """Create a new booking (PUBLIC - No authentication required)."""
        try:
            data = request.get_json()
            if not data:
                return {"message": "No data provided"}, 400

            # Validate required fields
            required_fields = ["name", "phone", "email", "serviceType", "date"]
            for field in required_fields:
                if field not in data or not data[field]:
                    return {"message": f"Missing required field: {field}"}, 400

            # Validate email format (basic)
            email = data['email'].strip()
            if '@' not in email or '.' not in email:
                return {"message": "Invalid email format"}, 400

            # Validate and parse date
            try:
                preferred_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
                # Check if date is not in the past
                if preferred_date < date.today():
                    return {"message": "Booking date cannot be in the past"}, 400
            except ValueError:
                return {"message": "Invalid date format. Use YYYY-MM-DD"}, 400

            # Validate and parse time if provided
            preferred_time = None
            if data.get('time'):
                try:
                    time_str = data['time'].strip()
                    # Handle HH:MM:SS format (strip seconds)
                    if time_str.count(':') == 2:
                        time_str = ':'.join(time_str.split(':')[:2])
                    preferred_time = datetime.strptime(time_str, '%H:%M').time()
                except ValueError:
                    return {"message": "Invalid time format. Use HH:MM"}, 400

            # Create Booking instance
            booking = Booking(
                client_name=data['name'].strip(),
                client_phone=data['phone'].strip(),
                client_email=email,
                service_type=data['serviceType'],
                preferred_date=preferred_date,
                preferred_time=preferred_time,
                location=data.get('location', '').strip() if data.get('location') else None,
                budget_range=data.get('budget', '').strip() if data.get('budget') else None,
                additional_notes=data.get('notes', '').strip() if data.get('notes') else None,
                status=BookingStatus.PENDING
            )

            db.session.add(booking)
            db.session.commit()
            
            logger.info(f"New booking created: {booking.id} - {booking.client_name} - {booking.service_type}")
            
            # Send confirmation email to client
            try:
                client_email_html = booking_confirmation_template(booking)
                client_email_sent = send_email(
                    recipient=booking.client_email,
                    subject=f"Booking Confirmation - {current_app.config['BUSINESS_NAME']}",
                    html_body=client_email_html
                )
                
                if client_email_sent:
                    logger.info(f"Confirmation email sent to client: {booking.client_email}")
                else:
                    logger.warning(f"Failed to send confirmation email to client: {booking.client_email}")
            except Exception as email_error:
                logger.error(f"Error sending client confirmation email: {str(email_error)}")
            
            # Send alert email to admin
            try:
                admin_email_html = admin_booking_alert_template(booking)
                admin_email_sent = send_email(
                    recipient=current_app.config['ADMIN_EMAIL'],
                    subject=f"🔔 New Booking Alert - {booking.service_type}",
                    html_body=admin_email_html
                )
                
                if admin_email_sent:
                    logger.info(f"Alert email sent to admin: {current_app.config['ADMIN_EMAIL']}")
                else:
                    logger.warning(f"Failed to send alert email to admin")
            except Exception as email_error:
                logger.error(f"Error sending admin alert email: {str(email_error)}")
            
            return {
                "message": "Booking request submitted successfully", 
                "booking": booking.as_dict(), 
                "id": booking.id
            }, 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating booking: {str(e)}")
            return {"message": "An error occurred while processing your booking"}, 500

    @jwt_required()
    def get(self, booking_id=None):
        """Retrieve a booking by ID (ADMIN only)."""
        try:
            identity = get_jwt_identity()
            user = User.query.get(identity)
            
            if not user or user.role != UserRole.ADMIN:
                return {"message": "Only admins can view bookings"}, 403

            if not booking_id:
                return {"message": "Booking ID is required"}, 400

            booking = Booking.query.get(booking_id)
            if not booking:
                return {"message": "Booking not found"}, 404
            
            return booking.as_dict(), 200
            
        except (OperationalError, SQLAlchemyError) as e:
            logger.error(f"Database error: {str(e)}")
            return {"message": "Database connection error"}, 500
        except Exception as e:
            logger.error(f"Error fetching booking: {str(e)}")
            return {"message": "Error fetching booking"}, 500

    @jwt_required()
    def put(self, booking_id):
        """Update an existing booking (ADMIN only)."""
        try:
            identity = get_jwt_identity()
            user = User.query.get(identity)
            
            if not user or user.role != UserRole.ADMIN:
                return {"message": "Only admins can update bookings"}, 403

            booking = Booking.query.get(booking_id)
            if not booking:
                return {"message": "Booking not found"}, 404

            data = request.get_json()
            if not data:
                return {"message": "No data provided"}, 400

            logger.info(f"Updating booking {booking_id} with data: {data}")

            # Track if status changed for email notification
            status_changed = False
            old_status = booking.status
            old_status_name = old_status.value if old_status else None

            # Update client information
            if "client_name" in data:
                booking.client_name = data['client_name'].strip()
            
            if "client_phone" in data:
                booking.client_phone = data['client_phone'].strip()
            
            if "client_email" in data:
                email = data['client_email'].strip()
                if '@' not in email or '.' not in email:
                    return {"message": "Invalid email format"}, 400
                booking.client_email = email
            
            # Update booking details
            if "service_type" in data:
                booking.service_type = data['service_type']
            
            if "preferred_date" in data:
                try:
                    preferred_date = datetime.strptime(data['preferred_date'], '%Y-%m-%d').date()
                    booking.preferred_date = preferred_date
                except ValueError as e:
                    logger.error(f"Invalid date format: {data['preferred_date']} - {str(e)}")
                    return {"message": "Invalid date format. Use YYYY-MM-DD"}, 400
            
            if "preferred_time" in data:
                if data['preferred_time']:
                    try:
                        # Handle both string time and already formatted time
                        if isinstance(data['preferred_time'], str):
                            time_str = data['preferred_time'].strip()
                            
                            # Handle HH:MM:SS format (strip seconds)
                            if time_str.count(':') == 2:
                                time_str = ':'.join(time_str.split(':')[:2])
                            
                            # Now parse HH:MM format
                            preferred_time = datetime.strptime(time_str, '%H:%M').time()
                        else:
                            # If it's already a time object or something else
                            preferred_time = data['preferred_time']
                        booking.preferred_time = preferred_time
                    except (ValueError, TypeError) as e:
                        logger.error(f"Invalid time format: {data['preferred_time']} - {str(e)}")
                        return {"message": "Invalid time format. Use HH:MM or HH:MM:SS"}, 400
                else:
                    booking.preferred_time = None
            
            if "location" in data:
                booking.location = data['location'].strip() if data['location'] else None
            
            if "budget_range" in data:
                booking.budget_range = data['budget_range'].strip() if data['budget_range'] else None
            
            if "additional_notes" in data:
                booking.additional_notes = data['additional_notes'].strip() if data['additional_notes'] else None
            
            # Update status and handle status-specific timestamps
            if "status" in data:
                try:
                    # Handle both string status and numeric status
                    status_value = data['status']
                    if isinstance(status_value, str):
                        new_status = BookingStatus[status_value.upper()]
                    elif isinstance(status_value, int):
                        # Assuming status is stored as integer enum in database
                        new_status = BookingStatus(status_value)
                    else:
                        return {"message": "Status must be a string or integer"}, 400
                    
                    if new_status != old_status:
                        status_changed = True
                        booking.status = new_status
                        
                        # Set timestamps based on status changes
                        current_time = datetime.now(timezone.utc)
                        if new_status == BookingStatus.CONFIRMED and old_status != BookingStatus.CONFIRMED:
                            booking.confirmed_at = current_time
                        elif new_status == BookingStatus.COMPLETED and old_status != BookingStatus.COMPLETED:
                            booking.completed_at = current_time
                        elif new_status == BookingStatus.CANCELLED:
                            # Optionally set cancelled_at timestamp if you have that field
                            pass
                        
                except (KeyError, ValueError) as e:
                    logger.error(f"Invalid status value: {data['status']} - {str(e)}")
                    valid_statuses = ', '.join([s.value for s in BookingStatus])
                    return {
                        "message": f"Invalid status. Must be one of: {valid_statuses}"
                    }, 400
            
            # Update assignment
            if "assigned_to" in data:
                if data['assigned_to']:
                    assigned_user = User.query.get(data['assigned_to'])
                    if not assigned_user:
                        return {"message": "Assigned user not found"}, 404
                    booking.assigned_to = data['assigned_to']
                else:
                    booking.assigned_to = None
            
            # Update internal notes
            if "internal_notes" in data:
                booking.internal_notes = data['internal_notes'].strip() if data['internal_notes'] else None

            # Update the updated_at timestamp
            booking.updated_at = datetime.now(timezone.utc)

            db.session.commit()
            
            logger.info(f"Booking updated by admin {user.email}: {booking.id}")
            
            # Send status update email to client if status changed
            if status_changed:
                try:
                    new_status_name = booking.status.value
                    status_email_html = booking_status_update_template(
                        booking=booking,
                        old_status=old_status_name,
                        new_status=new_status_name
                    )
                    
                    status_email_sent = send_email(
                        recipient=booking.client_email,
                        subject=f"Booking Status Update - {current_app.config['BUSINESS_NAME']}",
                        html_body=status_email_html
                    )
                    
                    if status_email_sent:
                        logger.info(f"Status update email sent to client: {booking.client_email} (Status: {new_status_name})")
                    else:
                        logger.warning(f"Failed to send status update email to client: {booking.client_email}")
                        
                except Exception as email_error:
                    logger.error(f"Error sending status update email: {str(email_error)}")
            
            return {"message": "Booking updated successfully", "booking": booking.as_dict()}, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating booking {booking_id}: {str(e)}", exc_info=True)
            return {"message": f"An error occurred: {str(e)}"}, 500

    @jwt_required()
    def delete(self, booking_id):
        """Delete a booking (ADMIN only)."""
        try:
            identity = get_jwt_identity()
            user = User.query.get(identity)
            
            if not user or user.role != UserRole.ADMIN:
                return {"message": "Only admins can delete bookings"}, 403

            booking = Booking.query.get(booking_id)
            if not booking:
                return {"message": "Booking not found"}, 404

            booking_info = f"{booking.client_name} - {booking.service_type}"
            
            db.session.delete(booking)
            db.session.commit()
            
            logger.info(f"Booking deleted by admin {user.email}: {booking_info}")
            
            return {"message": "Booking deleted successfully"}, 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting booking id {booking_id}: {str(e)}", exc_info=True)
            return {"message": "An unexpected error occurred during booking deletion"}, 500


class AdminBookingsResource(Resource):
    """Resource for admins to manage all bookings with filtering and pagination."""
    
    @jwt_required()
    def get(self):
        """Retrieve all bookings for admin management with filters."""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)

            if not user or user.role != UserRole.ADMIN:
                return {"message": "Only admins can access this endpoint"}, 403

            # Get query parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            status = request.args.get('status', type=str)
            service_type = request.args.get('service_type', type=str)
            search = request.args.get('search', type=str)
            assigned_to = request.args.get('assigned_to', type=int)
            date_from = request.args.get('date_from', type=str)
            date_to = request.args.get('date_to', type=str)
            
            # Build query with filters
            query = Booking.query
            
            # Filter by status
            if status:
                try:
                    status_enum = BookingStatus[status.upper()]
                    query = query.filter_by(status=status_enum)
                except KeyError:
                    return {
                        "message": f"Invalid status. Must be one of: {', '.join([s.value for s in BookingStatus])}"
                    }, 400
            
            # Filter by service type
            if service_type:
                query = query.filter_by(service_type=service_type)
            
            # Filter by assigned user
            if assigned_to:
                query = query.filter_by(assigned_to=assigned_to)
            
            # Search by client name, email, or phone
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Booking.client_name.ilike(search_term),
                        Booking.client_email.ilike(search_term),
                        Booking.client_phone.ilike(search_term)
                    )
                )
            
            # Filter by date range
            if date_from:
                try:
                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                    query = query.filter(Booking.preferred_date >= date_from_obj)
                except ValueError:
                    return {"message": "Invalid date_from format. Use YYYY-MM-DD"}, 400
            
            if date_to:
                try:
                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                    query = query.filter(Booking.preferred_date <= date_to_obj)
                except ValueError:
                    return {"message": "Invalid date_to format. Use YYYY-MM-DD"}, 400
            
            # Order by created_at descending (newest first)
            query = query.order_by(Booking.created_at.desc())
            
            # Get bookings with pagination
            bookings = query.paginate(page=page, per_page=per_page, error_out=False)
            
            return {
                'bookings': [booking.as_dict() for booking in bookings.items],
                'total': bookings.total,
                'pages': bookings.pages,
                'current_page': bookings.page
            }, 200
            
        except Exception as e:
            logger.error(f"Error fetching admin bookings: {str(e)}")
            return {"message": "Error fetching bookings"}, 500


class BookingStatusResource(Resource):
    """Resource for handling booking status operations."""
    
    def get(self):
        """Get all booking statuses (PUBLIC)"""
        try:
            statuses = [
                {
                    "name": status.name,
                    "value": status.value
                }
                for status in BookingStatus
            ]
            
            return {"statuses": statuses}, 200
            
        except Exception as e:
            logger.error(f"Error fetching statuses: {str(e)}")
            return {"message": "Error fetching statuses"}, 500


class BookingStatsResource(Resource):
    """Resource for getting booking statistics."""
    
    @jwt_required()
    def get(self):
        """Get booking statistics for admin dashboard."""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)

            if not user or user.role != UserRole.ADMIN:
                return {"message": "Only admins can access this endpoint"}, 403

            # Get counts by status
            stats = {
                "total": Booking.query.count(),
                "pending": Booking.query.filter_by(status=BookingStatus.PENDING).count(),
                "confirmed": Booking.query.filter_by(status=BookingStatus.CONFIRMED).count(),
                "cancelled": Booking.query.filter_by(status=BookingStatus.CANCELLED).count(),
                "completed": Booking.query.filter_by(status=BookingStatus.COMPLETED).count(),
            }
            
            # Get recent bookings (last 7 days)
            seven_days_ago = datetime.now(timezone.utc).date() - timedelta(days=7)
            stats['recent'] = Booking.query.filter(
                Booking.created_at >= seven_days_ago
            ).count()
            
            # Get upcoming bookings
            today = date.today()
            stats['upcoming'] = Booking.query.filter(
                and_(
                    Booking.preferred_date >= today,
                    Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
                )
            ).count()
            
            return {"stats": stats}, 200
            
        except Exception as e:
            logger.error(f"Error fetching booking stats: {str(e)}")
            return {"message": "Error fetching statistics"}, 500


class NewBookingsCountResource(Resource):
    """Resource for getting the count of new/pending bookings."""
    
    @jwt_required()
    def get(self):
        """Get count of new (pending) bookings (ADMIN only)."""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)

            if not user or user.role != UserRole.ADMIN:
                return {"message": "Only admins can access this endpoint"}, 403

            # Count pending bookings
            new_bookings_count = Booking.query.filter_by(status=BookingStatus.PENDING).count()
            
            # Optionally, you can also get the count of unread/recent new bookings
            # For example, bookings created in the last 24 hours
            twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_new_count = Booking.query.filter(
                and_(
                    Booking.status == BookingStatus.PENDING,
                    Booking.created_at >= twenty_four_hours_ago
                )
            ).count()
            
            return {
                "new_bookings_count": new_bookings_count,
                "recent_new_count": recent_new_count,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, 200
            
        except Exception as e:
            logger.error(f"Error fetching new bookings count: {str(e)}")
            return {"message": "Error fetching new bookings count"}, 500


class BookingBulkActionResource(Resource):
    """Resource for bulk actions on bookings."""
    
    @jwt_required()
    def post(self):
        """Perform bulk actions on multiple bookings (ADMIN only)."""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)

            if not user or user.role != UserRole.ADMIN:
                return {"message": "Only admins can perform bulk actions"}, 403

            data = request.get_json()
            if not data or 'booking_ids' not in data or 'action' not in data:
                return {"message": "booking_ids and action are required"}, 400

            booking_ids = data['booking_ids']
            action = data['action']
            
            if not isinstance(booking_ids, list) or not booking_ids:
                return {"message": "booking_ids must be a non-empty list"}, 400

            bookings = Booking.query.filter(Booking.id.in_(booking_ids)).all()
            
            if not bookings:
                return {"message": "No bookings found with provided IDs"}, 404

            updated_count = 0
            email_sent_count = 0

            # Handle different bulk actions
            if action == 'update_status':
                if 'status' not in data:
                    return {"message": "status is required for update_status action"}, 400
                
                try:
                    new_status = BookingStatus[data['status'].upper()]
                except KeyError:
                    return {
                        "message": f"Invalid status. Must be one of: {', '.join([s.value for s in BookingStatus])}"
                    }, 400
                
                for booking in bookings:
                    old_status = booking.status
                    old_status_name = old_status.value if old_status else None
                    
                    booking.status = new_status
                    booking.updated_at = datetime.now(timezone.utc)
                    
                    # Update timestamps
                    if new_status == BookingStatus.CONFIRMED and old_status != BookingStatus.CONFIRMED:
                        booking.confirmed_at = datetime.now(timezone.utc)
                    elif new_status == BookingStatus.COMPLETED and old_status != BookingStatus.COMPLETED:
                        booking.completed_at = datetime.now(timezone.utc)
                    
                    updated_count += 1
                    
                    # Send status update email if status changed
                    if old_status != new_status:
                        try:
                            new_status_name = booking.status.value
                            status_email_html = booking_status_update_template(
                                booking=booking,
                                old_status=old_status_name,
                                new_status=new_status_name
                            )
                            
                            if send_email(
                                recipient=booking.client_email,
                                subject=f"Booking Status Update - {current_app.config['BUSINESS_NAME']}",
                                html_body=status_email_html
                            ):
                                email_sent_count += 1
                                logger.info(f"Bulk status update email sent to: {booking.client_email}")
                        except Exception as email_error:
                            logger.error(f"Error sending bulk status email to {booking.client_email}: {str(email_error)}")
            
            elif action == 'assign':
                if 'assigned_to' not in data:
                    return {"message": "assigned_to is required for assign action"}, 400
                
                if data['assigned_to']:
                    assigned_user = User.query.get(data['assigned_to'])
                    if not assigned_user:
                        return {"message": "Assigned user not found"}, 404
                
                for booking in bookings:
                    booking.assigned_to = data['assigned_to']
                    booking.updated_at = datetime.now(timezone.utc)
                    updated_count += 1
            
            elif action == 'delete':
                for booking in bookings:
                    db.session.delete(booking)
                    updated_count += 1
                
                db.session.commit()
                logger.info(f"Bulk delete: {updated_count} bookings deleted by admin {user.email}")
                return {"message": f"{updated_count} bookings deleted successfully"}, 200
            
            else:
                return {"message": f"Unknown action: {action}"}, 400

            db.session.commit()
            logger.info(f"Bulk action '{action}' performed on {updated_count} bookings by admin {user.email}")
            
            response_message = f"Bulk action completed successfully"
            if email_sent_count > 0:
                response_message += f" ({email_sent_count} emails sent)"
            
            return {
                "message": response_message,
                "updated_count": updated_count,
                "emails_sent": email_sent_count
            }, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error performing bulk action: {str(e)}")
            return {"message": "An error occurred during bulk action"}, 500


def register_booking_resources(api):
    """Registers the BookingResource routes with Flask-RESTful API."""
    # Public endpoint
    api.add_resource(BookingResource, 
                     "/bookings",  # POST (public)
                     "/bookings/<int:booking_id>")  # GET, PUT, DELETE (admin)
    
    # Admin endpoints
    api.add_resource(AdminBookingsResource, "/admin/bookings")
    api.add_resource(BookingStatsResource, "/admin/bookings/stats")
    api.add_resource(NewBookingsCountResource, "/admin/bookings/new-count")
    api.add_resource(BookingBulkActionResource, "/admin/bookings/bulk-action")
    
    # Public utility endpoints
    api.add_resource(BookingStatusResource, "/booking-statuses")