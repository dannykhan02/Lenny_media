import logging
from datetime import datetime, timedelta, date
from decimal import Decimal
from sqlalchemy import func, or_
from typing import List, Dict, Optional, Tuple

from app import db
from app.models.quote import QuoteRequest, QuoteStatus
from app.models import User, UserRole

# Import email functionality
from . import (
    send_email,
    get_client_confirmation_email,
    get_admin_alert_email,
    get_client_reschedule_email,
    get_client_cancellation_email,
    get_quote_sent_email,
    get_quote_accepted_email,
    get_quote_rejected_email
)

# Import quote helpers with pricing functions
from app.models.quote_helpers import (
    enrich_selected_services,
    validate_service_selection,
    calculate_price_estimate,
    re_enrich_services_if_needed
)

logger = logging.getLogger(__name__)

# Constants
MAX_QUOTES_PER_DAY = 5
QUOTE_EXPIRY_DAYS = 30
# UPDATED: Match frontend STUDIO_HOURS (all 11:00 opening)
STUDIO_HOURS = {
    'monday': {'start': '08:00', 'end': '21:00'},
    'tuesday': {'start': '08:00', 'end': '21:00'},
    'wednesday': {'start': '08:00', 'end': '21:00'},
    'thursday': {'start': '08:30', 'end': '21:00'},
    'friday': {'start': '08:00', 'end': '21:00'},
    'saturday': {'start': '08:00', 'end': '21:00'}, # Estimated based on "Open now" status
    'sunday': {'start': '11:00', 'end': '21:00'}
}


class QuoteService:
    """Service class for handling quote-related business logic."""
    
    @staticmethod
    def _ensure_services_enriched(quote: QuoteRequest) -> None:
        """
        Ensure quote's selected_services have full pricing data.
        Re-enriches services if they're missing price information.
        
        This handles cases where:
        1. Old quotes were created before enrichment was implemented
        2. Services were stored with minimal data (id, title, category only)
        """
        if not quote.selected_services:
            return
        
        # Check if services are already enriched
        # If first service has price_min/price_max, assume all are enriched
        first_service = quote.selected_services[0] if quote.selected_services else {}
        
        # If already enriched, skip
        if first_service.get('price_min') is not None or first_service.get('price_max') is not None:
            return
        
        # Re-enrich services
        try:
            enriched_services = enrich_selected_services(
                quote.selected_services,
                db.session
            )
            
            # Update the quote with enriched services
            if enriched_services:
                quote.selected_services = enriched_services
                db.session.commit()
                logger.info(f"Re-enriched services for quote #{quote.id}")
        except Exception as e:
            logger.error(f"Failed to re-enrich services for quote #{quote.id}: {str(e)}")
            # Don't fail the request, just log the error
    
    @staticmethod
    def _parse_event_datetime(data: dict) -> Tuple:
        """Parse and validate event_date and event_time from request data."""
        event_date = None
        event_time = None
        
        # Parse event_date
        if data.get("event_date"):
            try:
                event_date = datetime.strptime(data["event_date"], "%Y-%m-%d").date()
                if event_date < date.today():
                    return {"message": "Event date cannot be in the past"}, 400
            except ValueError:
                return {"message": "Invalid event_date format. Use YYYY-MM-DD"}, 400
        
        # Parse event_time
        if data.get("event_time"):
            try:
                # Try parsing with seconds first
                event_time = datetime.strptime(data["event_time"], "%H:%M:%S").time()
            except ValueError:
                try:
                    # Try parsing without seconds
                    event_time = datetime.strptime(data["event_time"], "%H:%M").time()
                except ValueError:
                    return {"message": "Invalid event_time format. Use HH:MM or HH:MM:SS"}, 400
        
        return event_date, event_time
    
    @staticmethod
    def delete_quote(quote_id: int, user: User) -> Tuple[Dict, int]:
        """Delete a quote request. ADMIN ONLY."""
        if not user or user.role != UserRole.ADMIN:
            return {"message": "Only admins can delete quote requests"}, 403

        quote = QuoteRequest.query.get(quote_id)
        if not quote:
            return {"message": "Quote request not found"}, 404

        try:
            db.session.delete(quote)
            db.session.commit()
            
            logger.info(f"Quote request {quote_id} deleted by admin {user.email}")
            
            return {
                "message": "Quote request deleted successfully",
                "quote_id": quote_id
            }, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting quote request: {str(e)}")
            return {"error": "An error occurred while deleting the quote request"}, 500
    
    @staticmethod
    def cleanup_quotes(action_type: str, target_date: Optional[str], user: User) -> Tuple[Dict, int]:
        """Clean up old quotes or manage overcrowded days. ADMIN ONLY."""
        if not user or user.role != UserRole.ADMIN:
            return {"message": "Only admins can perform cleanup operations"}, 403

        try:
            if action_type == 'old_quotes':
                # Delete quotes older than QUOTE_EXPIRY_DAYS
                cutoff_date = datetime.utcnow() - timedelta(days=QUOTE_EXPIRY_DAYS)
                old_quotes = QuoteRequest.query.filter(
                    QuoteRequest.created_at < cutoff_date,
                    QuoteRequest.status.in_([QuoteStatus.PENDING, QuoteStatus.REJECTED])
                ).all()
                
                deleted_count = len(old_quotes)
                for quote in old_quotes:
                    db.session.delete(quote)
                
                db.session.commit()
                
                return {
                    "message": f"Successfully deleted {deleted_count} old quotes",
                    "deleted_count": deleted_count
                }, 200
                
            elif action_type == 'overcrowded_day' and target_date:
                # Delete excess quotes for a specific day
                try:
                    date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
                except ValueError:
                    return {"message": "Invalid date format. Use YYYY-MM-DD"}, 400
                
                quotes_on_day = QuoteRequest.query.filter(
                    QuoteRequest.event_date == date_obj,
                    QuoteRequest.status.in_([QuoteStatus.PENDING, QuoteStatus.SENT])
                ).order_by(QuoteRequest.created_at.asc()).all()
                
                if len(quotes_on_day) <= MAX_QUOTES_PER_DAY:
                    return {
                        "message": f"Day is not overcrowded. Current count: {len(quotes_on_day)}"
                    }, 200
                
                # Keep first MAX_QUOTES_PER_DAY, delete the rest
                excess_quotes = quotes_on_day[MAX_QUOTES_PER_DAY:]
                deleted_count = len(excess_quotes)
                
                for quote in excess_quotes:
                    db.session.delete(quote)
                
                db.session.commit()
                
                return {
                    "message": f"Successfully deleted {deleted_count} excess quotes for {target_date}",
                    "deleted_count": deleted_count,
                    "kept_count": MAX_QUOTES_PER_DAY
                }, 200
            
            else:
                return {"message": "Invalid cleanup type or missing date parameter"}, 400
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during cleanup: {str(e)}")
            return {"error": "An error occurred during cleanup"}, 500

    @staticmethod
    def bulk_action(data: dict, user: User) -> Tuple[Dict, int]:
        """Perform bulk actions on multiple quotes. ADMIN ONLY."""
        if not user or user.role != UserRole.ADMIN:
            return {"message": "Only admins can perform bulk actions"}, 403

        try:
            action = data.get('action')
            quote_ids = data.get('quote_ids', [])
            
            if not action or not quote_ids:
                return {"message": "Missing required fields: action and quote_ids"}, 400
            
            if not isinstance(quote_ids, list):
                return {"message": "quote_ids must be an array"}, 400
            
            quotes = QuoteRequest.query.filter(QuoteRequest.id.in_(quote_ids)).all()
            
            if not quotes:
                return {"message": "No quotes found with provided IDs"}, 404
            
            success_count = 0
            
            if action == 'DELETE':
                for quote in quotes:
                    db.session.delete(quote)
                    success_count += 1
                
                db.session.commit()
                
                return {
                    "message": f"Successfully deleted {success_count} quotes",
                    "deleted_count": success_count
                }, 200
                
            elif action == 'UPDATE_STATUS':
                new_status = data.get('status')
                if not new_status:
                    return {"message": "Missing required field: status"}, 400
                
                try:
                    status_enum = QuoteStatus[new_status.upper()]
                except KeyError:
                    return {
                        "message": f"Invalid status. Must be one of: {', '.join([s.value for s in QuoteStatus])}"
                    }, 400
                
                for quote in quotes:
                    quote.status = status_enum
                    quote.updated_at = datetime.utcnow()
                    success_count += 1
                
                db.session.commit()
                
                return {
                    "message": f"Successfully updated {success_count} quotes to {status_enum.value}",
                    "updated_count": success_count
                }, 200
            
            else:
                return {"message": f"Invalid action: {action}"}, 400
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during bulk action: {str(e)}")
            return {"error": "An error occurred during bulk action"}, 500

    @staticmethod
    def _generate_verified_alternative_times(quote: QuoteRequest, max_suggestions: int = 5) -> Dict:
        """
        Generate VERIFIED alternative time suggestions that are:
        1. Within studio operating hours
        2. Not conflicting with other quotes
        3. On the same date as the original quote
        
        Returns a dictionary with available times and diagnostics.
        """
        if not quote.event_date or not quote.event_time:
            return {
                "success": False,
                "error": "Quote must have both event_date and event_time",
                "available_times": [],
                "diagnostics": {
                    "checked_slots": 0,
                    "within_hours": 0,
                    "conflict_free": 0
                }
            }
        
        # Get studio hours for this day
        day_of_week = quote.event_date.strftime('%A').lower()
        if day_of_week not in STUDIO_HOURS:
            return {
                "success": False,
                "error": f"No studio hours defined for {day_of_week.capitalize()}",
                "available_times": [],
                "diagnostics": {}
            }
        
        hours = STUDIO_HOURS[day_of_week]
        try:
            start_time = datetime.strptime(hours['start'], "%H:%M").time()
            end_time = datetime.strptime(hours['end'], "%H:%M").time()
        except (ValueError, KeyError) as e:
            logger.error(f"Invalid studio hours format for {day_of_week}: {e}")
            return {
                "success": False,
                "error": "Invalid studio hours configuration",
                "available_times": [],
                "diagnostics": {}
            }
        
        current_hour = quote.event_time.hour
        current_minute = quote.event_time.minute
        
        # Generate time slots to check (prioritize closer times first)
        time_offsets = [1, -1, 2, -2, 3, -3, 4, -4, 5, -5, 6, -6]
        checked_times = set()  # Avoid checking duplicates
        available_times = []
        
        # Diagnostics
        slots_checked = 0
        slots_within_hours = 0
        slots_conflict_free = 0
        rejected_reasons = []
        
        for offset in time_offsets:
            if len(available_times) >= max_suggestions:
                break
            
            # Calculate new time
            new_hour = (current_hour + offset) % 24
            new_time = datetime.strptime(f"{new_hour:02d}:{current_minute:02d}", "%H:%M").time()
            
            # Skip if already checked
            time_key = new_time.isoformat()
            if time_key in checked_times:
                continue
            checked_times.add(time_key)
            slots_checked += 1
            
            # Check 1: Within studio hours
            if new_time < start_time or new_time > end_time:
                rejected_reasons.append({
                    "time": time_key,
                    "reason": "Outside studio hours",
                    "studio_hours": f"{hours['start']}-{hours['end']}"
                })
                continue
            
            slots_within_hours += 1
            
            # Check 2: No time conflicts
            try:
                has_conflict, conflicting_quotes = QuoteService._check_time_conflicts(
                    quote.id, 
                    quote.event_date, 
                    new_time
                )
                
                if has_conflict:
                    rejected_reasons.append({
                        "time": time_key,
                        "reason": "Time slot occupied",
                        "conflicting_quotes": [q.id for q in conflicting_quotes]
                    })
                    continue
                
                slots_conflict_free += 1
                
                # This time is available!
                available_times.append({
                    "time": time_key,
                    "display": new_time.strftime("%I:%M %p"),  # 12-hour format
                    "offset_hours": offset,
                    "verified": True
                })
                
            except Exception as e:
                logger.error(f"Error checking conflicts for time {time_key}: {str(e)}")
                rejected_reasons.append({
                    "time": time_key,
                    "reason": "Error during validation",
                    "error": str(e)
                })
        
        # Build response
        return {
            "success": len(available_times) > 0,
            "error": None if available_times else "No alternative times available within studio hours",
            "available_times": available_times,
            "original_time": quote.event_time.isoformat(),
            "event_date": quote.event_date.isoformat(),
            "studio_hours": {
                "start": hours['start'],
                "end": hours['end'],
                "day": day_of_week.capitalize()
            },
            "diagnostics": {
                "checked_slots": slots_checked,
                "within_hours": slots_within_hours,
                "conflict_free": slots_conflict_free,
                "available_found": len(available_times),
                "rejected_count": len(rejected_reasons),
                "rejected_sample": rejected_reasons[:3]  # Show first 3 rejections
            }
        }

    @staticmethod
    def _process_quotes(quotes: List[QuoteRequest], has_conflicts_filter: Optional[str]) -> Tuple[List[Dict], List[Dict], List[QuoteRequest]]:
        """
        Enhanced version with verified alternative time suggestions.
        Process quotes and generate alerts with VERIFIED alternatives.
        
        FIXED: Always recalculate conflicts dynamically instead of relying on stored has_conflict value.
        """
        quotes_data = []
        alerts = []
        conflicting_quotes_list = []
        
        for quote in quotes:
            # ✅ ADD THIS: Ensure services are enriched with pricing data
            QuoteService._ensure_services_enriched(quote)
            
            quote_dict = quote.as_dict()
            
            # ✅ FIXED: ALWAYS recalculate conflicts dynamically on fetch
            has_conflict = False
            if quote.event_date and quote.event_time:
                has_conflict, _ = QuoteService._check_time_conflicts(
                    quote.id, 
                    quote.event_date, 
                    quote.event_time
                )
                # Only update the database if the conflict status has changed
                if has_conflict != quote.has_conflict:
                    quote.mark_conflict(has_conflict)
                    db.session.commit()
            else:
                # If no date/time, ensure no conflict flag
                if quote.has_conflict:
                    quote.mark_conflict(False)
                    db.session.commit()
            
            # ============================================
            # UPDATED: Calculate price estimate for each quote
            # ============================================
            if quote.selected_services:
                quote_dict['price_estimate'] = calculate_price_estimate(quote.selected_services)
            # ============================================
            
            # Generate alerts for conflicting quotes
            if has_conflict and quote.status in [QuoteStatus.PENDING, QuoteStatus.SENT]:
                conflicting_quotes = QuoteService._detect_time_conflicts(quote)
                if conflicting_quotes:
                    all_same_time = [quote] + conflicting_quotes
                    all_same_time.sort(key=lambda x: x.created_at)
                    
                    is_first = all_same_time[0].id == quote.id
                    
                    # Generate VERIFIED alternative times
                    alternatives_result = QuoteService._generate_verified_alternative_times(quote)
                    
                    quote_dict["time_conflict"] = {
                        "has_conflict": True,
                        "is_priority": is_first,
                        "conflicting_count": len(conflicting_quotes),
                        "conflicting_quote_ids": [q.id for q in conflicting_quotes],
                        "message": "First come, first serve - this quote has priority" if is_first 
                                  else "This time slot is occupied. Suggest alternative time to client.",
                        "verified_alternatives": alternatives_result if not is_first else None
                    }
                    
                    if not is_first and quote.status == QuoteStatus.PENDING:
                        conflicting_quotes_list.append(quote)
                        
                        # Build alert with verified alternatives
                        alert = {
                            "quote_id": quote.id,
                            "type": "TIME_CONFLICT",
                            "severity": "HIGH",
                            "client_name": quote.client_name,
                            "client_email": quote.client_email,
                            "event_date": quote.event_date.isoformat() if quote.event_date else None,
                            "event_time": quote.event_time.isoformat() if quote.event_time else None,
                            "message": f"⚠️ Quote #{quote.id} ({quote.client_name}) conflicts with Quote #{all_same_time[0].id}",
                            "priority_quote": all_same_time[0].id,
                            "suggested_action": "UPDATE_TIME",
                            "action_required": True,
                            "alternatives": alternatives_result
                        }
                        
                        # Add API call examples if alternatives are available
                        if alternatives_result['success'] and alternatives_result['available_times']:
                            first_alternative = alternatives_result['available_times'][0]['time']
                            alert["api_call"] = {
                                "method": "PUT",
                                "endpoint": f"/quotes/{quote.id}",
                                "payload": {
                                    "event_date": quote.event_date.isoformat(),
                                    "event_time": first_alternative,
                                    "status": "PENDING"
                                },
                                "all_verified_alternatives": [
                                    alt['time'] for alt in alternatives_result['available_times']
                                ],
                                "note": "All suggested times are verified available and within studio hours"
                            }
                        else:
                            # No alternatives available
                            alert["api_call"] = {
                                "method": "PUT",
                                "endpoint": f"/quotes/{quote.id}",
                                "note": "No alternative times available on this date. Consider rescheduling to another day.",
                                "suggested_action": "RESCHEDULE_DATE",
                                "alternative_payload": {
                                    "event_date": (quote.event_date + timedelta(days=1)).isoformat(),
                                    "status": "PENDING"
                                }
                            }
                        
                        alerts.append(alert)
            
            # Apply filter if requested
            if has_conflicts_filter:
                if has_conflicts_filter.lower() == 'true' and has_conflict:
                    quotes_data.append(quote_dict)
                elif has_conflicts_filter.lower() == 'false' and not has_conflict:
                    quotes_data.append(quote_dict)
            else:
                quotes_data.append(quote_dict)
        
        return quotes_data, alerts, conflicting_quotes_list

    @staticmethod
    def create_quote(data: dict) -> Tuple[Dict, int]:
        """Create a new quote request with service pricing enrichment."""
        try:
            # Validate required fields
            required_fields = ["client_name", "client_email", "client_phone", "selected_services"]
            for field in required_fields:
                if field not in data or not data[field]:
                    return {"message": f"Missing required field: {field}"}, 400

            # Validate email format
            if "@" not in data["client_email"]:
                return {"message": "Invalid email format"}, 400

            # ============================================
            # NEW: Validate and enrich services with pricing
            # ============================================
            is_valid, error_msg = validate_service_selection(
                data["selected_services"], 
                db.session
            )
            if not is_valid:
                return {"message": error_msg}, 400
            
            # Enrich services with full pricing information
            enriched_services = enrich_selected_services(
                data["selected_services"],
                db.session
            )
            
            if not enriched_services:
                return {"message": "No valid services found"}, 400
            
            # Calculate price estimate for reference
            price_estimate = calculate_price_estimate(enriched_services)
            
            # ============================================
            # END NEW SECTION
            # ============================================

            # Parse event_date and event_time
            event_date, event_time = QuoteService._parse_event_datetime(data)
            if isinstance(event_date, tuple):  # Error response
                return event_date
            
            # Validate studio hours strictly
            error_response, status_code = QuoteService._validate_studio_hours_strict(event_date, event_time)
            if error_response:
                return error_response, status_code
            
            # Check quote limit strictly
            error_response, suggested_date = QuoteService._check_quote_limit_strict(event_date)
            if error_response:
                return error_response, 400
            
            # Update event_date if suggested
            if suggested_date and suggested_date != event_date:
                event_date = suggested_date
                data["event_date"] = event_date.isoformat()
                if event_time:
                    day_of_week = event_date.strftime('%A').lower()
                    if day_of_week in STUDIO_HOURS:
                        hours = STUDIO_HOURS[day_of_week]
                        start_time = datetime.strptime(hours['start'], "%H:%M").time()
                        if event_time < start_time:
                            event_time = start_time
                            data["event_time"] = event_time.isoformat()
            
            # Check for time conflicts
            conflict_warning = None
            has_conflict = False
            conflicting_quotes = []
            if event_date and event_time:
                has_conflict, conflicting_quotes = QuoteService._check_time_conflicts(
                    None, event_date, event_time
                )
                if has_conflict:
                    conflict_warning = {
                        "message": "This time slot is already occupied by another quote request. Please choose a different time or date.",
                        "conflicting_quotes": len(conflicting_quotes)
                    }

            # ============================================
            # NEW: Store enriched services instead of raw input
            # ============================================
            quote_request = QuoteRequest(
                client_name=data["client_name"],
                client_email=data["client_email"],
                client_phone=data["client_phone"],
                company_name=data.get("company_name"),
                selected_services=enriched_services,  # Store enriched data
                event_date=event_date,
                event_time=event_time,
                event_location=data.get("event_location"),
                budget_range=data.get("budget_range"),
                project_description=data.get("project_description"),
                referral_source=data.get("referral_source"),
                status=QuoteStatus.PENDING
            )
            # ============================================
            # END NEW SECTION
            # ============================================

            quote_request.mark_conflict(has_conflict)
            db.session.add(quote_request)
            db.session.commit()
            
            logger.info(f"Quote request created: {quote_request.id} by {quote_request.client_name}")
            
            # Prepare data for email templates
            quote_data = quote_request.as_dict()
            quote_data['has_conflict'] = has_conflict
            quote_data['conflicting_count'] = len(conflicting_quotes)
            quote_data['conflicting_quotes'] = [q.id for q in conflicting_quotes]
            # ============================================
            # NEW: Add price estimate to quote data for emails
            # ============================================
            quote_data['price_estimate'] = price_estimate
            # ============================================
            
            # Send confirmation email to client
            email_status = {"client": False, "admin": False}
            try:
                logger.info(f"[EMAIL] Preparing client confirmation email for: {quote_request.client_email}")
                client_email_data = get_client_confirmation_email(quote_data)
                
                logger.info(f"[EMAIL] Sending client confirmation email...")
                client_email_sent = send_email(
                    recipient=client_email_data['recipient'],
                    subject=client_email_data['subject'],
                    html_body=client_email_data['html']
                )
                
                if client_email_sent:
                    email_status["client"] = True
                    logger.info(f"[EMAIL] ✅ SUCCESS: Client confirmation email sent to {quote_request.client_email}")
                else:
                    logger.error(f"[EMAIL] ❌ FAILED: Client confirmation email NOT sent to {quote_request.client_email}")
            except Exception as email_error:
                logger.error(f"[EMAIL] ❌ EXCEPTION: Client confirmation email failed: {str(email_error)}", exc_info=True)
            
            # Send alert email to admin
            try:
                logger.info(f"[EMAIL] Preparing admin alert email for quote #{quote_request.id}")
                admin_email_data = get_admin_alert_email(quote_data)
                
                logger.info(f"[EMAIL] Sending admin alert email...")
                admin_email_sent = send_email(
                    recipient=admin_email_data['recipient'],
                    subject=admin_email_data['subject'],
                    html_body=admin_email_data['html']
                )
                
                if admin_email_sent:
                    email_status["admin"] = True
                    logger.info(f"[EMAIL] ✅ SUCCESS: Admin alert email sent for quote #{quote_request.id}")
                else:
                    logger.error(f"[EMAIL] ❌ FAILED: Admin alert email NOT sent for quote #{quote_request.id}")
            except Exception as email_error:
                logger.error(f"[EMAIL] ❌ EXCEPTION: Admin alert email failed: {str(email_error)}", exc_info=True)
            
            response_data = {
                "message": "Quote request submitted successfully",
                "processing_info": {
                    "client_email": quote_request.client_email,
                    "admin_email": "admin@yourdomain.com",
                    "estimated_time": "We'll respond within 24 hours",
                    "client_email_sent": email_status["client"],
                    "admin_email_sent": email_status["admin"],
                    "price_estimate": price_estimate  # Include in response
                },
                "quote_request": quote_data,
                "id": quote_request.id
            }
            
            if conflict_warning:
                response_data["warning"] = conflict_warning
                return response_data, 409
            
            return response_data, 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating quote request: {str(e)}")
            return {"error": "An error occurred while submitting your quote request"}, 500

    @staticmethod
    def get_quote(quote_id: int, user: User) -> Tuple[Dict, int]:
        """
        UPDATED VERSION: Get a specific quote with price estimation and verified alternative times.
        """
        if not user or user.role != UserRole.ADMIN:
            return {"message": "Only admins can access quote requests"}, 403

        quote = QuoteRequest.query.get(quote_id)
        if not quote:
            return {"message": "Quote request not found"}, 404

        # ✅ ADD THIS: Ensure services are enriched with pricing data
        QuoteService._ensure_services_enriched(quote)

        # ✅ FIXED: Recalculate conflict status dynamically
        has_conflict = False
        if quote.event_date and quote.event_time:
            has_conflict, _ = QuoteService._check_time_conflicts(
                quote.id, 
                quote.event_date, 
                quote.event_time
            )
            # Update database if status changed
            if has_conflict != quote.has_conflict:
                quote.mark_conflict(has_conflict)
                db.session.commit()
        
        conflicts = []
        conflict_alerts = []
        if has_conflict and quote.event_date and quote.event_time:
            conflicting_quotes = QuoteService._detect_time_conflicts(quote)
            conflicts = [q.id for q in conflicting_quotes]
            
            if conflicts:
                # Generate VERIFIED alternatives
                alternatives_result = QuoteService._generate_verified_alternative_times(quote)
                
                # Generate actionable alert with verified alternatives
                alert = {
                    "type": "TIME_CONFLICT",
                    "message": f"⚠️ Quote #{quote.id} conflicts with {len(conflicts)} other quote(s) on same date/time",
                    "conflicting_quote_ids": conflicts,
                    "suggested_action": "UPDATE",
                    "action_endpoint": f"PUT /quotes/{quote.id}",
                    "verified_alternatives": alternatives_result
                }
                
                # Add specific action payload if alternatives exist
                if alternatives_result['success'] and alternatives_result['available_times']:
                    alert["action_payload"] = {
                        "event_date": quote.event_date.isoformat(),
                        "event_time": alternatives_result['available_times'][0]['time'],
                        "note": f"Change to verified available time: {alternatives_result['available_times'][0]['display']}"
                    }
                    alert["all_available_times"] = [
                        {
                            "time": alt['time'],
                            "display": alt['display'],
                            "offset_hours": alt['offset_hours']
                        }
                        for alt in alternatives_result['available_times']
                    ]
                else:
                    alert["action_payload"] = {
                        "event_date": (quote.event_date + timedelta(days=1)).isoformat(),
                        "note": "No available times on this date. Reschedule to next day."
                    }
                    alert["warning"] = alternatives_result['error']
                
                conflict_alerts.append(alert)
            
            # Check if time is outside studio hours
            error_response, _ = QuoteService._validate_studio_hours(quote.event_date, quote.event_time)
            if error_response:
                conflict_alerts.append({
                    "type": "OUTSIDE_STUDIO_HOURS",
                    "message": error_response["message"],
                    "suggested_start": error_response.get("suggested_start"),
                    "suggested_end": error_response.get("suggested_end"),
                    "suggested_action": "UPDATE_TIME",
                    "action_endpoint": f"PUT /quotes/{quote.id}",
                    "action_payload": {
                        "event_time": error_response.get("suggested_start"),
                        "note": "Change event_time to be within studio hours"
                    }
                })
        
        # Check if day has reached quote limit
        quote_count = QuoteRequest.query.filter(
            QuoteRequest.event_date == quote.event_date,
            QuoteRequest.status.in_([QuoteStatus.PENDING, QuoteStatus.SENT, QuoteStatus.ACCEPTED])
        ).count()
        
        if quote_count >= MAX_QUOTES_PER_DAY:
            conflict_alerts.append({
                "type": "QUOTE_LIMIT_REACHED",
                "message": f"⚠️ Maximum {MAX_QUOTES_PER_DAY} quotes reached for {quote.event_date.strftime('%A')}, {quote.event_date.strftime('%Y-%m-%d')}",
                "current_quote_count": quote_count,
                "max_quotes": MAX_QUOTES_PER_DAY,
                "suggested_action": "RESCHEDULE",
                "suggested_date": (quote.event_date + timedelta(days=1)).isoformat(),
                "note": "Consider rescheduling to the next available day"
            })
        
        response = quote.as_dict()
        
        # ============================================
        # UPDATED: Add price estimate to response
        # ============================================
        if quote.selected_services:
            response['price_estimate'] = calculate_price_estimate(quote.selected_services)
        # ============================================
        
        # ✅ FIXED: Use recalculated has_conflict instead of stored value
        response['has_conflict'] = has_conflict
        
        if conflicts:
            response["time_conflict"] = {
                "has_conflict": True,
                "conflicting_quote_ids": conflicts,
                "message": "This time slot conflicts with other quotes"
            }
        if conflict_alerts:
            response["alerts"] = conflict_alerts
        
        return response, 200

    @staticmethod
    def get_alternative_times(quote_id: int, user: User, max_suggestions: int = 5) -> Tuple[Dict, int]:
        """
        NEW ENDPOINT: Get verified alternative times for a specific quote.
        
        Usage: GET /quotes/{quote_id}/alternative-times?max_suggestions=5
        """
        if not user or user.role != UserRole.ADMIN:
            return {"message": "Only admins can access this endpoint"}, 403

        quote = QuoteRequest.query.get(quote_id)
        if not quote:
            return {"message": "Quote request not found"}, 404
        
        if not quote.event_date or not quote.event_time:
            return {
                "message": "Quote must have both event_date and event_time to generate alternatives",
                "quote_id": quote_id
            }, 400
        
        try:
            # Generate verified alternatives
            alternatives_result = QuoteService._generate_verified_alternative_times(
                quote, 
                max_suggestions=min(max_suggestions, 10)  # Cap at 10
            )
            
            # Add quote context
            response = {
                "quote_id": quote.id,
                "client_name": quote.client_name,
                "current_time": quote.event_time.isoformat(),
                "current_date": quote.event_date.isoformat(),
                **alternatives_result
            }
            
            return response, 200
            
        except Exception as e:
            logger.error(f"Error generating alternatives for quote {quote_id}: {str(e)}")
            return {
                "error": "Failed to generate alternative times",
                "details": str(e)
            }, 500

    @staticmethod
    def get_all_quotes(filters: dict, user: User) -> Tuple[Dict, int]:
        """Get all quotes with filters and pagination."""
        if not user or user.role != UserRole.ADMIN:
            return {"message": "Only admins can access quote requests"}, 403

        try:
            page = filters.get('page', 1)
            per_page = filters.get('per_page', 20)
            status_filter = filters.get('status')
            date_from = filters.get('date_from')
            date_to = filters.get('date_to')
            has_conflicts = filters.get('has_conflicts')
            assigned_to = filters.get('assigned_to')
            search = filters.get('search')

            # Build query
            query = QuoteRequest.query
            
            # Apply filters
            if status_filter:
                # Check if it's comma-separated (multiple statuses)
                if ',' in status_filter:
                    status_values = status_filter.split(',')
                    status_enums = []
                    invalid_statuses = []
                    
                    for status_value in status_values:
                        try:
                            status_enum = QuoteStatus[status_value.strip().upper()]
                            status_enums.append(status_enum)
                        except KeyError:
                            invalid_statuses.append(status_value.strip())
                    
                    if invalid_statuses:
                        return {
                            "message": f"Invalid status(es): {', '.join(invalid_statuses)}. Must be one of: {', '.join([s.value for s in QuoteStatus])}"
                        }, 400
                    
                    query = query.filter(QuoteRequest.status.in_(status_enums))
                else:
                    # Single status
                    try:
                        status_enum = QuoteStatus[status_filter.upper()]
                        query = query.filter_by(status=status_enum)
                    except KeyError:
                        return {
                            "message": f"Invalid status. Must be one of: {', '.join([s.value for s in QuoteStatus])}"
                        }, 400
            
            if date_from:
                try:
                    date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
                    query = query.filter(QuoteRequest.event_date >= date_from_obj)
                except ValueError:
                    return {"message": "Invalid date_from format. Use YYYY-MM-DD"}, 400
            
            if date_to:
                try:
                    date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
                    query = query.filter(QuoteRequest.event_date <= date_to_obj)
                except ValueError:
                    return {"message": "Invalid date_to format. Use YYYY-MM-DD"}, 400
            
            if assigned_to:
                query = query.filter_by(assigned_to=assigned_to)
            
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        QuoteRequest.client_name.ilike(search_term),
                        QuoteRequest.client_email.ilike(search_term),
                        QuoteRequest.client_phone.ilike(search_term),
                        QuoteRequest.company_name.ilike(search_term)
                    )
                )

            # Order by created_at descending
            query = query.order_by(QuoteRequest.created_at.desc())
            
            # Paginate
            quotes = query.paginate(page=page, per_page=per_page, error_out=False)
            
            # Process quotes using enhanced method with verified alternatives
            quotes_data, alerts, conflicting_quotes_list = QuoteService._process_quotes(
                quotes.items, has_conflicts
            )
            
            # Get business alerts
            busy_days = QuoteService._get_busy_days()
            overcrowded_alerts = QuoteService._get_overcrowded_alerts(busy_days)
            old_quotes_alerts = QuoteService._get_old_quotes_alerts()
            
            # Combine all alerts
            all_alerts = alerts + overcrowded_alerts + old_quotes_alerts
            
            # Summary statistics
            summary = QuoteService._get_summary_statistics(quotes.total, busy_days, old_quotes_alerts, all_alerts)
            summary["quote_limit_per_day"] = MAX_QUOTES_PER_DAY
            
            response = {
                'quotes': quotes_data,
                'total': quotes.total,
                'pages': quotes.pages,
                'current_page': quotes.page,
                'summary': summary
            }
            
            if all_alerts:
                # Sort by severity
                severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
                response['alerts'] = sorted(
                    all_alerts, 
                    key=lambda x: severity_order.get(x.get('severity', 'LOW'), 3)
                )
                response['alerts_summary'] = {
                    "total_alerts": len(all_alerts),
                    "high_priority": len([a for a in all_alerts if a.get('severity') == 'HIGH']),
                    "medium_priority": len([a for a in all_alerts if a.get('severity') == 'MEDIUM']),
                    "low_priority": len([a for a in all_alerts if a.get('severity') == 'LOW']),
                    "action_required": len([a for a in all_alerts if a.get('action_required')])
                }
            
            if has_conflicts and has_conflicts.lower() == 'true':
                response['message'] = f"Showing {len(quotes_data)} quotes with time conflicts"
                response['conflicting_quotes_count'] = len(quotes_data)
            
            return response, 200
            
        except Exception as e:
            logger.error(f"Error fetching quote requests: {str(e)}")
            return {"message": "Error fetching quote requests"}, 500

    # ============================================
    # UPDATE: Modify update_quote to handle service updates
    # ============================================
    @staticmethod
    def update_quote(quote_id: int, data: dict, user: User) -> Tuple[Dict, int]:
        """Update a quote request with comprehensive email notifications."""
        if not user or user.role != UserRole.ADMIN:
            return {"message": "Only admins can update quote requests"}, 403

        quote = QuoteRequest.query.get(quote_id)
        if not quote:
            return {"message": "Quote request not found"}, 404

        try:
            # Track changes for email notifications
            original_status = quote.status
            old_event_date = quote.event_date
            old_event_time = quote.event_time
            
            is_reschedule = data.get('is_reschedule', False)
            admin_note = data.get('admin_note', '')
            rejection_reason = data.get('rejection_reason', admin_note)
            
            status_changed = False
            new_status = None
            
            # ============================================
            # NEW: Handle service updates with validation
            # ============================================
            if "selected_services" in data:
                is_valid, error_msg = validate_service_selection(
                    data["selected_services"],
                    db.session
                )
                if not is_valid:
                    return {"message": error_msg}, 400
                
                # Enrich services before updating
                enriched_services = enrich_selected_services(
                    data["selected_services"],
                    db.session
                )
                quote.selected_services = enriched_services
                # Remove from data to avoid processing in _update_quote_fields
                data.pop("selected_services", None)
            # ============================================
            
            # Update event date if provided
            if "event_date" in data:
                result = QuoteService._update_event_date(quote, data["event_date"])
                if isinstance(result, tuple):
                    return result
            
            # Update event time if provided
            if "event_time" in data:
                result = QuoteService._update_event_time(quote, data["event_time"])
                if isinstance(result, tuple):
                    return result
                
                if quote.event_date and quote.event_time:
                    error_response, status_code = QuoteService._validate_studio_hours(quote.event_date, quote.event_time)
                    if error_response:
                        return error_response, status_code
            
            # Update conflict state if date/time changed
            if (quote.event_date != old_event_date) or (quote.event_time != old_event_time):
                QuoteService._update_conflict_state(quote)
            
            # Check for conflicts after update
            conflict_info = None
            if quote.event_date and quote.event_time and quote.has_conflict:
                conflicting_quotes = QuoteService._detect_time_conflicts(quote)
                if conflicting_quotes:
                    conflict_info = {
                        "warning": "⚠️ Updated time slot still conflicts with existing quotes",
                        "conflicting_quote_ids": [q.id for q in conflicting_quotes],
                        "conflicting_clients": [q.client_name for q in conflicting_quotes],
                        "suggestion": "Consider suggesting alternative times to client or updating conflicting quotes"
                    }
            
            # Update other fields
            update_errors = QuoteService._update_quote_fields(quote, data)
            if update_errors:
                return update_errors
            
            # Check if status changed
            if "status" in data:
                try:
                    new_status = QuoteStatus[data["status"].upper()]
                    if new_status != original_status:
                        status_changed = True
                except KeyError:
                    pass
            
            quote.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Quote request {quote_id} updated by admin {user.email}")
            
            # ========== EMAIL NOTIFICATION LOGIC ==========
            quote_data = quote.as_dict()
            # ============================================
            # NEW: Add price estimate to updated quote data
            # ============================================
            if quote.selected_services:
                quote_data['price_estimate'] = calculate_price_estimate(quote.selected_services)
            # ============================================
            
            email_sent = False
            email_type = None
            
            # Priority 1: Reschedule
            if is_reschedule:
                try:
                    email_type = "reschedule"
                    logger.info(f"[EMAIL] Preparing reschedule email for: {quote.client_email}")
                    email_data = get_client_reschedule_email(quote_data, admin_note)
                    
                    email_sent = send_email(
                        recipient=email_data['recipient'],
                        subject=email_data['subject'],
                        html_body=email_data['html']
                    )
                    
                    if email_sent:
                        logger.info(f"[EMAIL] ✅ SUCCESS: Reschedule email sent (Quote #{quote.id})")
                    else:
                        logger.error(f"[EMAIL] ❌ FAILED: Reschedule email NOT sent")
                except Exception as email_error:
                    logger.error(f"[EMAIL] ❌ EXCEPTION: Reschedule email failed: {str(email_error)}", exc_info=True)
            
            # Priority 2: Status change emails
            elif status_changed:
                try:
                    if new_status == QuoteStatus.SENT:
                        email_type = "quote_sent"
                        email_data = get_quote_sent_email(quote_data)
                        
                    elif new_status == QuoteStatus.ACCEPTED:
                        email_type = "quote_accepted"
                        email_data = get_quote_accepted_email(quote_data)
                        
                    elif new_status == QuoteStatus.REJECTED:
                        email_type = "quote_rejected"
                        email_data = get_quote_rejected_email(quote_data, rejection_reason)
                        
                    elif new_status == QuoteStatus.CANCELLED:
                        email_type = "cancellation"
                        cancellation_reason = data.get('cancellation_reason', admin_note)
                        email_data = get_client_cancellation_email(quote_data, cancellation_reason)
                    else:
                        email_type = None
                        email_data = None
                    
                    if email_data:
                        email_sent = send_email(
                            recipient=email_data['recipient'],
                            subject=email_data['subject'],
                            html_body=email_data['html']
                        )
                        
                        if email_sent:
                            logger.info(f"[EMAIL] ✅ SUCCESS: {email_type} email sent (Quote #{quote.id})")
                        else:
                            logger.error(f"[EMAIL] ❌ FAILED: {email_type} email NOT sent")
                            
                except Exception as email_error:
                    logger.error(f"[EMAIL] ❌ EXCEPTION: {email_type} email failed: {str(email_error)}", exc_info=True)
            
            response = {
                "message": "Quote request updated successfully",
                "processing_info": {
                    "email_sent": email_sent,
                    "email_type": email_type,
                    "recipient": quote.client_email if email_sent else None,
                    "status_changed": status_changed,
                    "old_status": original_status.value if original_status else None,
                    "new_status": new_status.value if new_status else None
                },
                "quote_request": quote.as_dict()
            }
            
            if conflict_info:
                response["conflict_info"] = conflict_info
            
            return response, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating quote request: {str(e)}")
            return {"error": "An error occurred while updating the quote request"}, 500

    @staticmethod
    def _detect_time_conflicts(quote: QuoteRequest) -> List[QuoteRequest]:
        """Detect time conflicts for a quote."""
        if not quote.event_date or not quote.event_time:
            return []
        
        return QuoteRequest.query.filter(
            QuoteRequest.event_date == quote.event_date,
            QuoteRequest.event_time == quote.event_time,
            QuoteRequest.id != quote.id,
            QuoteRequest.status.in_([
                QuoteStatus.PENDING,
                QuoteStatus.SENT,
                QuoteStatus.ACCEPTED
            ])
        ).order_by(QuoteRequest.created_at.asc()).all()

    @staticmethod
    def _check_time_conflicts(quote_id: Optional[int], event_date: date, event_time: datetime.time) -> Tuple[bool, List[QuoteRequest]]:
        """Check for time conflicts for a given date and time."""
        query = QuoteRequest.query.filter(
            QuoteRequest.event_date == event_date,
            QuoteRequest.event_time == event_time,
            QuoteRequest.status.in_([QuoteStatus.PENDING, QuoteStatus.SENT, QuoteStatus.ACCEPTED])
        )
        
        if quote_id:
            query = query.filter(QuoteRequest.id != quote_id)
        
        conflicting_quotes = query.all()
        return len(conflicting_quotes) > 0, conflicting_quotes

    @staticmethod
    def _update_conflict_state(quote: QuoteRequest):
        """Update conflict state for a quote."""
        if not quote.event_date or not quote.event_time:
            quote.mark_conflict(False)
            return
        
        has_conflict, _ = QuoteService._check_time_conflicts(quote.id, quote.event_date, quote.event_time)
        quote.mark_conflict(has_conflict)

    @staticmethod
    def _get_busy_days() -> List:
        """Get days with too many quotes."""
        busy_days = db.session.query(
            QuoteRequest.event_date,
            func.count(QuoteRequest.id).label('count')
        ).filter(
            QuoteRequest.event_date.isnot(None),
            QuoteRequest.status.in_([QuoteStatus.PENDING, QuoteStatus.SENT, QuoteStatus.ACCEPTED])
        ).group_by(
            QuoteRequest.event_date
        ).having(
            func.count(QuoteRequest.id) > MAX_QUOTES_PER_DAY
        ).all()
        
        return busy_days

    @staticmethod
    def _get_overcrowded_alerts(busy_days: List) -> List[Dict]:
        """Get alerts for overcrowded days."""
        alerts = []
        for busy_day in busy_days:
            quotes_on_day = QuoteRequest.query.filter(
                QuoteRequest.event_date == busy_day.event_date,
                QuoteRequest.status.in_([QuoteStatus.PENDING, QuoteStatus.SENT])
            ).order_by(QuoteRequest.created_at.desc()).all()
            
            excess_quotes = quotes_on_day[MAX_QUOTES_PER_DAY:] if len(quotes_on_day) > MAX_QUOTES_PER_DAY else []
            excess_quote_ids = [q.id for q in excess_quotes]
            
            alerts.append({
                "type": "OVERCROWDED_DAY",
                "severity": "MEDIUM",
                "date": busy_day.event_date.isoformat(),
                "quote_count": busy_day.count,
                "excess_count": len(excess_quotes),
                "message": f"⚠️ {busy_day.event_date.isoformat()} has {busy_day.count} quotes ({len(excess_quotes)} excess)",
                "suggested_action": "DELETE_EXCESS",
                "action_required": True,
                "excess_quote_ids": excess_quote_ids,
                "excess_quotes_details": [
                    {
                        "id": q.id,
                        "client_name": q.client_name,
                        "client_email": q.client_email,
                        "created_at": q.created_at.isoformat()
                    }
                    for q in excess_quotes
                ],
                "api_call": {
                    "method": "DELETE",
                    "endpoint": "/quotes/cleanup",
                    "query_params": {
                        "type": "overcrowded_day",
                        "date": busy_day.event_date.isoformat()
                    },
                    "note": f"This will delete {len(excess_quotes)} excess quotes, keeping the first {MAX_QUOTES_PER_DAY}"
                }
            })
        
        return alerts

    @staticmethod
    def _get_old_quotes_alerts() -> List[Dict]:
        """Get alerts for old quotes."""
        cutoff_date = datetime.utcnow() - timedelta(days=QUOTE_EXPIRY_DAYS)
        old_quotes = QuoteRequest.query.filter(
            QuoteRequest.created_at < cutoff_date,
            QuoteRequest.status.in_([QuoteStatus.PENDING, QuoteStatus.REJECTED])
        ).all()
        
        if not old_quotes:
            return []
        
        old_quote_ids = [q.id for q in old_quotes]
        
        return [{
            "type": "OLD_QUOTES",
            "severity": "LOW",
            "quote_count": len(old_quotes),
            "message": f"⚠️ {len(old_quotes)} quotes are {QUOTE_EXPIRY_DAYS}+ days old and pending/rejected",
            "suggested_action": "DELETE_OLD",
            "action_required": False,
            "old_quote_ids": old_quote_ids,
            "old_quotes_sample": [
                {
                    "id": q.id,
                    "client_name": q.client_name,
                    "created_at": q.created_at.isoformat(),
                    "age_days": (datetime.utcnow() - q.created_at).days
                }
                for q in old_quotes[:10]
            ],
            "api_call": {
                "method": "DELETE",
                "endpoint": "/quotes/cleanup",
                "query_params": {
                    "type": "old_quotes"
                },
                "note": f"This will delete all {len(old_quotes)} quotes older than {QUOTE_EXPIRY_DAYS} days"
            }
        }]

    @staticmethod
    def _get_summary_statistics(total_quotes: int, busy_days: List, old_quotes_alerts: List[Dict], alerts: List[Dict]) -> Dict:
        """Get summary statistics for quotes."""
        summary = {
            "total_quotes": QuoteRequest.query.count(),
            "pending_count": QuoteRequest.query.filter_by(status=QuoteStatus.PENDING).count(),
            "sent_count": QuoteRequest.query.filter_by(status=QuoteStatus.SENT).count(),
            "accepted_count": QuoteRequest.query.filter_by(status=QuoteStatus.ACCEPTED).count(),
            "rejected_count": QuoteRequest.query.filter_by(status=QuoteStatus.REJECTED).count(),
            "cancelled_count": QuoteRequest.query.filter_by(status=QuoteStatus.CANCELLED).count(),
            "total_quotes": total_quotes,
            "time_conflicts_count": len([a for a in alerts if a.get('type') == 'TIME_CONFLICT']),
            "overcrowded_days_count": len(busy_days),
            "old_quotes_count": old_quotes_alerts[0]['quote_count'] if old_quotes_alerts else 0,
            "action_required_count": len([a for a in alerts if a.get('action_required')])
        }
        return summary

    @staticmethod
    def _update_event_date(quote: QuoteRequest, event_date_str: Optional[str]) -> Optional[Tuple[Dict, int]]:
        """Update event date on quote."""
        if event_date_str:
            try:
                new_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
                if new_date < date.today():
                    return {"message": "Event date cannot be in the past"}, 400
                quote.event_date = new_date
            except ValueError:
                return {"message": "Invalid event_date format. Use YYYY-MM-DD"}, 400
        else:
            quote.event_date = None
        return None

    @staticmethod
    def _update_event_time(quote: QuoteRequest, event_time_str: Optional[str]) -> Optional[Tuple[Dict, int]]:
        """Update event time on quote."""
        if event_time_str:
            try:
                # Try parsing with seconds first
                new_time = datetime.strptime(event_time_str, "%H:%M:%S").time()
            except ValueError:
                try:
                    # Try parsing without seconds
                    new_time = datetime.strptime(event_time_str, "%H:%M").time()
                except ValueError:
                    return {"message": "Invalid event_time format. Use HH:MM or HH:MM:SS"}, 400
            quote.event_time = new_time
        else:
            quote.event_time = None
        return None

    @staticmethod
    def _update_quote_fields(quote: QuoteRequest, data: dict) -> Optional[Tuple[Dict, int]]:
        """Update various fields on quote."""
        if "client_name" in data:
            quote.client_name = data["client_name"]
        
        if "client_email" in data:
            if "@" not in data["client_email"]:
                return {"message": "Invalid email format"}, 400
            quote.client_email = data["client_email"]
        
        if "client_phone" in data:
            quote.client_phone = data["client_phone"]
        
        if "company_name" in data:
            quote.company_name = data["company_name"]
        
        # Note: selected_services is now handled separately in update_quote method
        # So we skip it here to avoid double processing
        
        if "event_location" in data:
            quote.event_location = data["event_location"]
        
        if "budget_range" in data:
            quote.budget_range = data["budget_range"]
        
        if "project_description" in data:
            quote.project_description = data["project_description"]
        
        if "status" in data:
            try:
                status_enum = QuoteStatus[data["status"].upper()]
                
                # Handle cancellation using model method
                if status_enum == QuoteStatus.CANCELLED:
                    quote.cancel()
                else:
                    quote.status = status_enum
                
                # Set quote_sent_at if status is being set to SENT
                if status_enum == QuoteStatus.SENT and not quote.quote_sent_at:
                    quote.quote_sent_at = datetime.utcnow()
                    
            except KeyError:
                return {
                    "message": f"Invalid status. Must be one of: {', '.join([s.value for s in QuoteStatus])}"
                }, 400
        
        if "quoted_amount" in data:
            if data["quoted_amount"] is not None:
                try:
                    quoted_amount = Decimal(str(data["quoted_amount"]))
                    if quoted_amount < 0:
                        return {"message": "Quoted amount cannot be negative"}, 400
                    quote.quoted_amount = quoted_amount
                except (ValueError, TypeError):
                    return {"message": "Invalid quoted_amount format"}, 400
            else:
                quote.quoted_amount = None
        
        if "quote_details" in data:
            quote.quote_details = data["quote_details"]
        
        if "valid_until" in data:
            if data["valid_until"]:
                try:
                    valid_until = datetime.strptime(data["valid_until"], "%Y-%m-%d").date()
                    quote.valid_until = valid_until
                except ValueError:
                    return {"message": "Invalid valid_until format. Use YYYY-MM-DD"}, 400
            else:
                quote.valid_until = None
        
        if "assigned_to" in data:
            quote.assigned_to = data["assigned_to"]
        
        return None

    @staticmethod
    def _validate_studio_hours(event_date: date, event_time: datetime.time) -> Tuple[Optional[Dict], int]:
        """Validate that event time is within studio operating hours."""
        if not event_date or not event_time:
            return None, 200
        
        # Get day of week
        day_of_week = event_date.strftime('%A').lower()
        
        # Check if day exists in studio hours
        if day_of_week not in STUDIO_HOURS:
            return {"message": f"Studio hours not defined for {day_of_week.capitalize()}"}, 400
        
        # Get studio hours for this day
        hours = STUDIO_HOURS[day_of_week]
        start_time = datetime.strptime(hours['start'], "%H:%M").time()
        end_time = datetime.strptime(hours['end'], "%H:%M").time()
        
        # Check if event time is within operating hours
        if event_time < start_time or event_time > end_time:
            # UPDATED: Use 'open'/'close' keys to match frontend expectations
            return {
                "message": f"⚠️ Studio is closed during this time. Please select a time between {hours['start']}-{hours['end']}",
                "studio_hours": {
                    "open": hours['start'],   # Map 'start' to 'open'
                    "close": hours['end'],    # Map 'end' to 'close'
                    "day": day_of_week.capitalize()
                },
                "suggested_start": hours['start'],
                "suggested_end": hours['end'],
                "current_time": event_time.isoformat()
            }, 400
        
        return None, 200

    @staticmethod
    def _validate_studio_hours_strict(event_date: date, event_time: datetime.time) -> Tuple[Optional[Dict], int]:
        """Strict validation for quote creation - returns error for invalid times."""
        if not event_date or not event_time:
            return {"message": "Event date and time are required"}, 400
        
        # Get day of week
        day_of_week = event_date.strftime('%A').lower()
        
        # Check if day exists in studio hours
        if day_of_week not in STUDIO_HOURS:
            return {"message": f"Studio hours not defined for {day_of_week.capitalize()}"}, 400
        
        # Get studio hours for this day
        hours = STUDIO_HOURS[day_of_week]
        start_time = datetime.strptime(hours['start'], "%H:%M").time()
        end_time = datetime.strptime(hours['end'], "%H:%M").time()
        
        # Check if event time is within operating hours
        if event_time < start_time or event_time > end_time:
            # UPDATED: Use 'open'/'close' keys to match frontend expectations
            return {
                "message": f"⚠️ Studio is closed during this time. Please select a time between {hours['start']}-{hours['end']}",
                "studio_hours": {
                    "open": hours['start'],   # Map 'start' to 'open'
                    "close": hours['end'],    # Map 'end' to 'close'
                    "day": day_of_week.capitalize()
                },
                "suggested_start": hours['start'],
                "suggested_end": hours['end'],
                "current_time": event_time.isoformat()
            }, 400
        
        return None, 200

    @staticmethod
    def _check_quote_limit_strict(event_date: date) -> Tuple[Optional[Dict], Optional[date]]:
        """Strict check for quote limit - rejects quotes for full days."""
        # Count quotes for the requested date
        quote_count = QuoteRequest.query.filter(
            QuoteRequest.event_date == event_date,
            QuoteRequest.status.in_([QuoteStatus.PENDING, QuoteStatus.SENT, QuoteStatus.ACCEPTED])
        ).count()
        
        if quote_count >= MAX_QUOTES_PER_DAY:
            # Find next available day within the next 30 days
            current_date = event_date
            for _ in range(30):  # Look ahead 30 days
                current_date = current_date + timedelta(days=1)
                day_of_week = current_date.strftime('%A').lower()
                
                # Check if day has studio hours and within limit
                if day_of_week in STUDIO_HOURS:
                    next_day_count = QuoteRequest.query.filter(
                        QuoteRequest.event_date == current_date,
                        QuoteRequest.status.in_([QuoteStatus.PENDING, QuoteStatus.SENT, QuoteStatus.ACCEPTED])
                    ).count()
                    
                    if next_day_count < MAX_QUOTES_PER_DAY:
                        return {
                            "message": f"⚠️ Maximum {MAX_QUOTES_PER_DAY} quotes reached for {event_date.strftime('%A')}, {event_date.strftime('%Y-%m-%d')}. Please choose a different date.",
                            "suggested_date": current_date.isoformat(),
                            "suggested_day": current_date.strftime('%A'),
                            "current_quote_count": quote_count,
                            "max_quotes": MAX_QUOTES_PER_DAY,
                            "rescheduling_required": True
                        }, current_date
        
            return {
                "message": f"⚠️ Maximum {MAX_QUOTES_PER_DAY} quotes reached and no available days in the next 30 days.",
                "current_quote_count": quote_count,
                "max_quotes": MAX_QUOTES_PER_DAY,
                "rescheduling_required": True
            }, None
        
        return None, event_date