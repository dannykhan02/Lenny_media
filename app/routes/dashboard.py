"""
Dashboard Statistics Resource
Provides comprehensive statistics for admin dashboard visualizations
Plus notification and quote summary endpoints for navbar
"""

import logging
from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import func, and_, or_, extract
from sqlalchemy.exc import SQLAlchemyError

from ..models import User, UserRole
from ..models.booking import Booking, BookingStatus
from ..models.quote import QuoteRequest, QuoteStatus
from ..models.service import Service, ServiceCategory
from .. import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DashboardStatsResource(Resource):
    """
    Comprehensive dashboard statistics for admin panel
    Returns aggregated data across all major entities
    """
    
    @jwt_required()
    def get(self):
        """
        Get comprehensive dashboard statistics
        Query params:
        - period: 'week', 'month', 'quarter', 'year', 'all' (default: 'month')
        - date_from: YYYY-MM-DD (optional, overrides period)
        - date_to: YYYY-MM-DD (optional, overrides period)
        """
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)

            if not user or user.role != UserRole.ADMIN:
                return {"message": "Only admins can access dashboard statistics"}, 403

            # Get query parameters
            period = request.args.get('period', 'month')
            date_from_str = request.args.get('date_from')
            date_to_str = request.args.get('date_to')

            # Calculate date range
            date_to = datetime.now(timezone.utc).date()
            
            if date_from_str and date_to_str:
                # Custom date range
                try:
                    date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
                    date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
                except ValueError:
                    return {"message": "Invalid date format. Use YYYY-MM-DD"}, 400
            else:
                # Predefined periods
                if period == 'week':
                    date_from = date_to - timedelta(days=7)
                elif period == 'month':
                    date_from = date_to - timedelta(days=30)
                elif period == 'quarter':
                    date_from = date_to - timedelta(days=90)
                elif period == 'year':
                    date_from = date_to - timedelta(days=365)
                else:  # 'all'
                    date_from = None

            # Collect all statistics
            stats = {
                "overview": self._get_overview_stats(date_from, date_to),
                "bookings": self._get_booking_stats(date_from, date_to),
                "quotes": self._get_quote_stats(date_from, date_to),
                "revenue": self._get_revenue_stats(date_from, date_to),
                "services": self._get_service_stats(date_from, date_to),
                "trends": self._get_trends_data(date_from, date_to),
                "team": self._get_team_stats(),
                "recent_activity": self._get_recent_activity(),
                "period": {
                    "type": period,
                    "from": date_from.isoformat() if date_from else None,
                    "to": date_to.isoformat()
                }
            }

            return stats, 200

        except SQLAlchemyError as e:
            logger.error(f"Database error fetching dashboard stats: {str(e)}")
            return {"message": "Database error occurred"}, 500
        except Exception as e:
            logger.error(f"Error fetching dashboard stats: {str(e)}")
            return {"message": "Error fetching dashboard statistics"}, 500

    def _get_overview_stats(self, date_from, date_to):
        """Get high-level overview statistics"""
        base_query_date = date_from is not None
        
        # Total counts
        total_bookings = Booking.query.count()
        total_quotes = QuoteRequest.query.count()
        
        # Period-specific counts
        if base_query_date:
            period_bookings = Booking.query.filter(
                Booking.created_at >= date_from,
                Booking.created_at <= date_to
            ).count()
            period_quotes = QuoteRequest.query.filter(
                QuoteRequest.created_at >= date_from,
                QuoteRequest.created_at <= date_to
            ).count()
        else:
            period_bookings = total_bookings
            period_quotes = total_quotes

        # Active/Pending counts
        pending_bookings = Booking.query.filter_by(status=BookingStatus.PENDING).count()
        pending_quotes = QuoteRequest.query.filter_by(status=QuoteStatus.PENDING).count()

        return {
            "total": {
                "bookings": total_bookings,
                "quotes": total_quotes,
                "clients": self._get_unique_client_count()
            },
            "period": {
                "bookings": period_bookings,
                "quotes": period_quotes
            },
            "pending": {
                "bookings": pending_bookings,
                "quotes": pending_quotes,
                "total": pending_bookings + pending_quotes
            }
        }

    def _get_booking_stats(self, date_from, date_to):
        """Get detailed booking statistics"""
        query = Booking.query
        
        if date_from:
            query = query.filter(Booking.created_at >= date_from)
            query = query.filter(Booking.created_at <= date_to)

        # Status breakdown
        status_counts = {}
        for status in BookingStatus:
            count = query.filter_by(status=status).count()
            status_counts[status.value] = count

        # Service type breakdown
        service_breakdown = db.session.query(
            Booking.service_type,
            func.count(Booking.id).label('count')
        ).filter(
            Booking.created_at >= date_from if date_from else True,
            Booking.created_at <= date_to if date_from else True
        ).group_by(Booking.service_type).all()

        # Upcoming bookings
        upcoming = Booking.query.filter(
            Booking.preferred_date >= date.today(),
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
        ).count()

        # This week's bookings
        week_start = date.today() - timedelta(days=date.today().weekday())
        week_end = week_start + timedelta(days=6)
        this_week = Booking.query.filter(
            Booking.preferred_date >= week_start,
            Booking.preferred_date <= week_end
        ).count()

        return {
            "by_status": status_counts,
            "by_service": {item.service_type: item.count for item in service_breakdown},
            "upcoming": upcoming,
            "this_week": this_week,
            "conversion_rate": self._calculate_booking_conversion_rate(date_from, date_to)
        }

    def _get_quote_stats(self, date_from, date_to):
        """Get detailed quote request statistics"""
        query = QuoteRequest.query
        
        if date_from:
            query = query.filter(QuoteRequest.created_at >= date_from)
            query = query.filter(QuoteRequest.created_at <= date_to)

        # Status breakdown
        status_counts = {}
        for status in QuoteStatus:
            count = query.filter_by(status=status).count()
            status_counts[status.value] = count

        # Quotes with conflicts
        conflicted_quotes = query.filter_by(has_conflict=True).count()

        # Average quote amount (where quoted_amount is not null)
        avg_quote = db.session.query(
            func.avg(QuoteRequest.quoted_amount)
        ).filter(
            QuoteRequest.quoted_amount.isnot(None),
            QuoteRequest.created_at >= date_from if date_from else True
        ).scalar()

        # Response time (average time to send quote)
        avg_response_time = db.session.query(
            func.avg(
                func.extract('epoch', QuoteRequest.quote_sent_at - QuoteRequest.created_at)
            )
        ).filter(
            QuoteRequest.quote_sent_at.isnot(None),
            QuoteRequest.created_at >= date_from if date_from else True
        ).scalar()

        return {
            "by_status": status_counts,
            "with_conflicts": conflicted_quotes,
            "average_quote_amount": float(avg_quote) if avg_quote else 0,
            "average_response_time_hours": float(avg_response_time / 3600) if avg_response_time else 0,
            "acceptance_rate": self._calculate_quote_acceptance_rate(date_from, date_to)
        }

    def _get_revenue_stats(self, date_from, date_to):
        """Get revenue-related statistics"""
        # Total quoted amount (accepted quotes)
        total_quoted = db.session.query(
            func.sum(QuoteRequest.quoted_amount)
        ).filter(
            QuoteRequest.status == QuoteStatus.ACCEPTED,
            QuoteRequest.created_at >= date_from if date_from else True,
            QuoteRequest.created_at <= date_to if date_from else True
        ).scalar() or 0

        # Potential revenue (pending quotes)
        potential_revenue = db.session.query(
            func.sum(QuoteRequest.quoted_amount)
        ).filter(
            QuoteRequest.status.in_([QuoteStatus.PENDING, QuoteStatus.SENT]),
            QuoteRequest.quoted_amount.isnot(None),
            QuoteRequest.created_at >= date_from if date_from else True
        ).scalar() or 0

        # Revenue by service category (from accepted quotes)
        revenue_by_service = db.session.query(
            QuoteRequest.selected_services,
            func.sum(QuoteRequest.quoted_amount).label('revenue')
        ).filter(
            QuoteRequest.status == QuoteStatus.ACCEPTED,
            QuoteRequest.quoted_amount.isnot(None),
            QuoteRequest.created_at >= date_from if date_from else True
        ).group_by(QuoteRequest.selected_services).all()

        return {
            "total_quoted": float(total_quoted),
            "potential_revenue": float(potential_revenue),
            "by_service": [
                {"service": item.selected_services, "revenue": float(item.revenue)}
                for item in revenue_by_service
            ]
        }

    def _get_service_stats(self, date_from, date_to):
        """Get service-related statistics"""
        # Active services count
        active_services = Service.query.filter_by(is_active=True).count()
        featured_services = Service.query.filter_by(is_featured=True).count()

        # Services by category
        photography_services = Service.query.filter_by(
            category=ServiceCategory.PHOTOGRAPHY,
            is_active=True
        ).count()
        videography_services = Service.query.filter_by(
            category=ServiceCategory.VIDEOGRAPHY,
            is_active=True
        ).count()

        return {
            "active_services": active_services,
            "featured_services": featured_services,
            "by_category": {
                "photography": photography_services,
                "videography": videography_services
            }
        }

    def _get_trends_data(self, date_from, date_to):
        """Get trend data for charts"""
        if not date_from:
            date_from = date.today() - timedelta(days=30)

        # Daily bookings trend
        bookings_trend = db.session.query(
            func.date(Booking.created_at).label('date'),
            func.count(Booking.id).label('count')
        ).filter(
            Booking.created_at >= date_from,
            Booking.created_at <= date_to
        ).group_by(func.date(Booking.created_at)).order_by('date').all()

        # Daily quotes trend
        quotes_trend = db.session.query(
            func.date(QuoteRequest.created_at).label('date'),
            func.count(QuoteRequest.id).label('count')
        ).filter(
            QuoteRequest.created_at >= date_from,
            QuoteRequest.created_at <= date_to
        ).group_by(func.date(QuoteRequest.created_at)).order_by('date').all()

        return {
            "bookings": [
                {
                    "date": item.date if isinstance(item.date, str) else item.date.isoformat(), 
                    "count": item.count
                }
                for item in bookings_trend
            ],
            "quotes": [
                {
                    "date": item.date if isinstance(item.date, str) else item.date.isoformat(), 
                    "count": item.count
                }
                for item in quotes_trend
            ]
        }

    def _get_team_stats(self):
        """Get team member statistics"""
        # Total users by role
        role_breakdown = {}
        for role in UserRole:
            count = User.query.filter_by(role=role, is_active=True).count()
            role_breakdown[role.value] = count

        # Assignment statistics
        assigned_bookings = db.session.query(
            User.id,
            User.full_name,
            func.count(Booking.id).label('booking_count')
        ).join(Booking, Booking.assigned_to == User.id).filter(
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
        ).group_by(User.id, User.full_name).all()

        return {
            "by_role": role_breakdown,
            "total_active": User.query.filter_by(is_active=True).count(),
            "workload": [
                {
                    "user_id": item.id,
                    "name": item.full_name,
                    "active_bookings": item.booking_count
                }
                for item in assigned_bookings
            ]
        }

    def _get_recent_activity(self):
        """Get recent activity across all entities"""
        # Recent bookings (last 5)
        recent_bookings = Booking.query.order_by(
            Booking.created_at.desc()
        ).limit(5).all()

        # Recent quotes (last 5)
        recent_quotes = QuoteRequest.query.order_by(
            QuoteRequest.created_at.desc()
        ).limit(5).all()

        return {
            "bookings": [
                {
                    "id": b.id,
                    "client_name": b.client_name,
                    "service": b.service_type,
                    "status": b.status.value,
                    "created_at": b.created_at.isoformat()
                }
                for b in recent_bookings
            ],
            "quotes": [
                {
                    "id": q.id,
                    "client_name": q.client_name,
                    "status": q.status.value,
                    "amount": float(q.quoted_amount) if q.quoted_amount else None,
                    "created_at": q.created_at.isoformat()
                }
                for q in recent_quotes
            ]
        }

    # Helper calculation methods
    def _get_unique_client_count(self):
        """Calculate unique clients across all entities"""
        booking_emails = db.session.query(Booking.client_email).distinct()
        quote_emails = db.session.query(QuoteRequest.client_email).distinct()
        
        # Combine and count unique emails
        all_emails = set()
        for email in booking_emails:
            all_emails.add(email[0])
        for email in quote_emails:
            all_emails.add(email[0])
        
        return len(all_emails)

    def _calculate_booking_conversion_rate(self, date_from, date_to):
        """Calculate booking conversion rate (confirmed/total)"""
        query = Booking.query
        if date_from:
            query = query.filter(Booking.created_at >= date_from)
            query = query.filter(Booking.created_at <= date_to)
        
        total = query.count()
        if total == 0:
            return 0
        
        confirmed = query.filter_by(status=BookingStatus.CONFIRMED).count()
        return round((confirmed / total) * 100, 2)

    def _calculate_quote_acceptance_rate(self, date_from, date_to):
        """Calculate quote acceptance rate"""
        query = QuoteRequest.query
        if date_from:
            query = query.filter(QuoteRequest.created_at >= date_from)
            query = query.filter(QuoteRequest.created_at <= date_to)
        
        sent = query.filter_by(status=QuoteStatus.SENT).count()
        accepted = query.filter_by(status=QuoteStatus.ACCEPTED).count()
        total = sent + accepted
        
        if total == 0:
            return 0
        
        return round((accepted / total) * 100, 2)


# =====================================================
# NEW: Notification Count Resource (for navbar badge)
# =====================================================
class NotificationCountResource(Resource):
    """
    Get unread notification count for navbar badge
    Counts actionable items from both bookings and quotes:
    - Pending bookings
    - Pending quotes
    - Quotes with conflicts
    - Old pending quotes (>24hrs)
    - Quotes needing follow-up (>7 days)
    """
    
    @jwt_required()
    def get(self):
        """Get count of actionable items (alerts) - bookings + quotes"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)

            if not user or user.role != UserRole.ADMIN:
                return {"message": "Only admins can access notifications"}, 403

            # Count alerts from BOTH bookings and quotes
            alert_count = 0
            
            # ====================
            # BOOKING ALERTS
            # ====================
            # Pending bookings need attention
            pending_bookings = Booking.query.filter_by(
                status=BookingStatus.PENDING
            ).count()
            alert_count += pending_bookings
            
            # ====================
            # QUOTE ALERTS
            # ====================
            # Count all PENDING quotes (need to be processed)
            pending_quotes = QuoteRequest.query.filter_by(
                status=QuoteStatus.PENDING
            ).count()
            alert_count += pending_quotes
            
            # Count SENT quotes with conflicts (not already counted in pending)
            conflicted_sent_quotes = QuoteRequest.query.filter_by(
                has_conflict=True,
                status=QuoteStatus.SENT
            ).count()
            alert_count += conflicted_sent_quotes
            
            # Total conflicted quotes (for breakdown - both pending and sent)
            total_conflicted_quotes = QuoteRequest.query.filter_by(
                has_conflict=True
            ).filter(
                QuoteRequest.status.in_([QuoteStatus.PENDING, QuoteStatus.SENT])
            ).count()
            
            # Old pending quotes (for breakdown - informational only)
            yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
            old_pending = QuoteRequest.query.filter_by(
                status=QuoteStatus.PENDING
            ).filter(
                QuoteRequest.created_at < yesterday
            ).count()
            
            # Quotes needing follow-up (for breakdown - informational only)
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            needs_followup = QuoteRequest.query.filter_by(
                status=QuoteStatus.SENT
            ).filter(
                QuoteRequest.quote_sent_at < week_ago
            ).count()

            return {
                "count": alert_count,
                "breakdown": {
                    "pending_bookings": pending_bookings,
                    "pending_quotes": pending_quotes,
                    "conflicted_sent_quotes": conflicted_sent_quotes,
                    "total_conflicts": total_conflicted_quotes,
                    "old_pending": old_pending,
                    "needs_followup": needs_followup
                }
            }, 200

        except SQLAlchemyError as e:
            logger.error(f"Database error fetching notification count: {str(e)}")
            return {"message": "Database error occurred"}, 500
        except Exception as e:
            logger.error(f"Error fetching notification count: {str(e)}")
            return {"message": "Error fetching notification count"}, 500


# =====================================================
# NEW: Quote Summary Resource (for navbar badges)
# =====================================================
class QuoteSummaryResource(Resource):
    """
    Get quick quote statistics for navbar badges
    Returns counts needed for badge display
    """
    
    @jwt_required()
    def get(self):
        """Get quick quote statistics"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)

            if not user or user.role != UserRole.ADMIN:
                return {"message": "Only admins can access quote summary"}, 403

            # Status counts
            pending_count = QuoteRequest.query.filter_by(
                status=QuoteStatus.PENDING
            ).count()
            
            sent_count = QuoteRequest.query.filter_by(
                status=QuoteStatus.SENT
            ).count()
            
            accepted_count = QuoteRequest.query.filter_by(
                status=QuoteStatus.ACCEPTED
            ).count()
            
            # Conflict count (active quotes with conflicts)
            conflict_count = QuoteRequest.query.filter_by(
                has_conflict=True
            ).filter(
                QuoteRequest.status.in_([QuoteStatus.PENDING, QuoteStatus.SENT])
            ).count()
            
            # Action required (pending + conflicts)
            action_required = pending_count + conflict_count

            return {
                "pending_count": pending_count,
                "sent_count": sent_count,
                "accepted_count": accepted_count,
                "time_conflicts_count": conflict_count,
                "action_required_count": action_required,
                "total_quotes": QuoteRequest.query.count()
            }, 200

        except SQLAlchemyError as e:
            logger.error(f"Database error fetching quote summary: {str(e)}")
            return {"message": "Database error occurred"}, 500
        except Exception as e:
            logger.error(f"Error fetching quote summary: {str(e)}")
            return {"message": "Error fetching quote summary"}, 500


# =====================================================
# Register all resources
# =====================================================
def register_dashboard_resources(api):
    """Register dashboard statistics and navbar helper endpoints"""
    # Main dashboard stats
    api.add_resource(DashboardStatsResource, "/admin/dashboard/stats")
    
    # Navbar helper endpoints
    api.add_resource(NotificationCountResource, "/notifications/unread-count")
    api.add_resource(QuoteSummaryResource, "/quotes/summary")