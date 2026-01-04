import json
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from ..models import User
from ..models.quote import QuoteStatus, QuoteRequest
from ..services import QuoteService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuoteRequestResource(Resource):
    """Resource for handling individual quote requests."""
    
    def post(self):
        """Create a new quote request (PUBLIC - clients can submit quotes)."""
        data = request.get_json()
        return QuoteService.create_quote(data)

    @jwt_required()
    def get(self, quote_id=None):
        """Retrieve quote request(s) with actionable conflict alerts. ADMIN ONLY."""
        identity = get_jwt_identity()
        user = User.query.get(identity)
        
        if quote_id:
            return QuoteService.get_quote(quote_id, user)
        else:
            # Get all quotes with filters
            filters = {
                'page': request.args.get('page', 1, type=int),
                'per_page': request.args.get('per_page', 20, type=int),
                'status': request.args.get('status', type=str),
                'date_from': request.args.get('date_from', type=str),
                'date_to': request.args.get('date_to', type=str),
                'has_conflicts': request.args.get('has_conflicts', type=str),
                'assigned_to': request.args.get('assigned_to', type=int),
                'search': request.args.get('search', type=str)
            }
            return QuoteService.get_all_quotes(filters, user)

    @jwt_required()
    def put(self, quote_id):
        """Update a quote request. ADMIN ONLY."""
        identity = get_jwt_identity()
        user = User.query.get(identity)
        data = request.get_json()
        
        return QuoteService.update_quote(quote_id, data, user)

    @jwt_required()
    def delete(self, quote_id):
        """Delete a quote request. ADMIN ONLY."""
        identity = get_jwt_identity()
        user = User.query.get(identity)
        
        return QuoteService.delete_quote(quote_id, user)


class QuoteAlternativeTimesResource(Resource):
    """Resource for getting verified alternative times for a quote. ADMIN ONLY."""
    
    @jwt_required()
    def get(self, quote_id):
        """Get verified alternative times for a specific quote."""
        identity = get_jwt_identity()
        user = User.query.get(identity)
        
        # Get max_suggestions from query params
        max_suggestions = request.args.get('max_suggestions', default=5, type=int)
        
        # Call service
        return QuoteService.get_alternative_times(
            quote_id=quote_id,
            user=user,
            max_suggestions=max_suggestions
        )


class QuoteCleanupResource(Resource):
    """Resource for cleaning up old and overcrowded quotes. ADMIN ONLY."""
    
    @jwt_required()
    def delete(self):
        """Delete old quotes (30+ days old) and manage overcrowded days. ADMIN ONLY."""
        identity = get_jwt_identity()
        user = User.query.get(identity)
        
        action_type = request.args.get('type', 'old_quotes')
        target_date = request.args.get('date', type=str)
        
        return QuoteService.cleanup_quotes(action_type, target_date, user)


class QuoteBulkActionResource(Resource):
    """Resource for performing bulk actions on quotes. ADMIN ONLY."""
    
    @jwt_required()
    def post(self):
        """Perform bulk actions on multiple quotes (DELETE, UPDATE_STATUS). ADMIN ONLY."""
        identity = get_jwt_identity()
        user = User.query.get(identity)
        data = request.get_json()
        
        return QuoteService.bulk_action(data, user)


class QuoteStatusResource(Resource):
    """Resource for getting available quote statuses."""
    
    def get(self):
        """Get all quote statuses (PUBLIC)."""
        try:
            statuses = [
                {
                    "name": status.name,
                    "value": status.value
                }
                for status in QuoteStatus
            ]
            
            return {"statuses": statuses}, 200
            
        except Exception as e:
            logger.error(f"Error fetching statuses: {str(e)}")
            return {"message": "Error fetching statuses"}, 500


def register_quote_resources(api):
    """Registers the QuoteRequest routes with Flask-RESTful API."""
    api.add_resource(QuoteRequestResource, "/quotes", "/quotes/<int:quote_id>")
    api.add_resource(QuoteAlternativeTimesResource, "/quotes/<int:quote_id>/alternative-times")  # NEW ENDPOINT
    api.add_resource(QuoteCleanupResource, "/quotes/cleanup")
    api.add_resource(QuoteBulkActionResource, "/quotes/bulk-action")
    
    api.add_resource(QuoteStatusResource, "/quote-statuses")