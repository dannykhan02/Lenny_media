import json
from flask import request, jsonify
from flask_restful import Resource
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from decimal import Decimal

try:
    from slugify import slugify
except ImportError:
    # Fallback if python-slugify is not installed
    import re
    def slugify(text):
        """Simple slugify function as fallback"""
        text = str(text).lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text

from ..models import User, UserRole
from ..models.service import Service, ServiceCategory
from .. import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceResource(Resource):
    """Resource for handling individual services and service listings."""
    
    def get(self, service_id=None):
        """Retrieve a service by ID or return all active services if no ID is provided."""
        if service_id:
            try:
                # For public access, only return active services
                service = Service.query.filter_by(id=service_id, is_active=True).first()
                if service:
                    return service.as_dict(), 200
                return {"message": "Service not found"}, 404
            except (OperationalError, SQLAlchemyError) as e:
                logger.error(f"Database error: {str(e)}")
                return {"message": "Database connection error"}, 500
        
        # Get query parameters for pagination and filtering
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        category = request.args.get('category', type=str)
        is_featured = request.args.get('is_featured', type=bool)
        
        try:
            # Build query with filters - only active services for public
            query = Service.query.filter_by(is_active=True)
            
            if category:
                try:
                    category_enum = ServiceCategory[category.upper()]
                    query = query.filter_by(category=category_enum)
                except KeyError:
                    return {
                        "message": f"Invalid category. Must be one of: {', '.join([c.value for c in ServiceCategory])}"
                    }, 400
            
            if is_featured is not None:
                query = query.filter_by(is_featured=is_featured)
            
            # Order by display_order and created_at
            query = query.order_by(Service.display_order.asc(), Service.created_at.desc())
            
            # Get services with pagination
            services = query.paginate(page=page, per_page=per_page, error_out=False)
            
            if not services.items:
                return {
                    'services': [],
                    'total': 0,
                    'pages': 0,
                    'current_page': page
                }
            
            return {
                'services': [service.as_dict() for service in services.items],
                'total': services.total,
                'pages': services.pages,
                'current_page': services.page
            }, 200
            
        except (OperationalError, SQLAlchemyError) as e:
            logger.error(f"Database error: {str(e)}")
            return {"message": "Database connection error"}, 500
        except Exception as e:
            logger.error(f"Error fetching services: {str(e)}")
            return {"message": "Error fetching services"}, 500

    @jwt_required()
    def post(self):
        """Create a new service (Only admins can create services)."""
        try:
            identity = get_jwt_identity()
            user = User.query.get(identity)
            
            if not user or user.role != UserRole.ADMIN:
                return {"message": "Only admins can create services"}, 403

            data = request.get_json()
            if not data:
                return {"message": "No data provided"}, 400

            # Validate required fields
            required_fields = ["category", "title"]
            for field in required_fields:
                if field not in data:
                    return {"message": f"Missing field: {field}"}, 400

            # Validate category
            try:
                category_enum = ServiceCategory[data["category"].upper()]
            except KeyError:
                return {
                    "message": f"Invalid category. Must be one of: {', '.join([c.value for c in ServiceCategory])}"
                }, 400

            # Generate slug from title if not provided
            slug = data.get('slug', slugify(data['title']))
            
            # Check if slug already exists
            existing_service = Service.query.filter_by(slug=slug).first()
            if existing_service:
                return {"message": "Service with this slug already exists"}, 400

            # Validate prices if provided
            price_min = None
            price_max = None
            
            if 'price_min' in data and data['price_min'] is not None:
                try:
                    price_min = Decimal(str(data['price_min']))
                    if price_min < 0:
                        return {"message": "Price minimum cannot be negative"}, 400
                except (ValueError, TypeError):
                    return {"message": "Invalid price_min format"}, 400
            
            if 'price_max' in data and data['price_max'] is not None:
                try:
                    price_max = Decimal(str(data['price_max']))
                    if price_max < 0:
                        return {"message": "Price maximum cannot be negative"}, 400
                except (ValueError, TypeError):
                    return {"message": "Invalid price_max format"}, 400
            
            # Validate price range
            if price_min and price_max and price_min > price_max:
                return {"message": "price_min cannot be greater than price_max"}, 400

            # Validate display_order
            display_order = 0
            if 'display_order' in data:
                try:
                    display_order = int(data['display_order'])
                except (ValueError, TypeError):
                    return {"message": "Invalid display_order format"}, 400

            # Create Service instance
            service = Service(
                category=category_enum,
                title=data['title'],
                slug=slug,
                description=data.get('description'),
                price_min=price_min,
                price_max=price_max,
                price_display=data.get('price_display'),
                features=data.get('features', []),
                is_active=data.get('is_active', True),
                is_featured=data.get('is_featured', False),
                display_order=display_order,
                icon_name=data.get('icon_name')
            )

            db.session.add(service)
            db.session.commit()
            
            logger.info(f"Service created by admin {user.email}: {service.title}")
            
            return {
                "message": "Service created successfully", 
                "service": service.as_dict(), 
                "id": service.id
            }, 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating service: {str(e)}")
            return {"error": str(e)}, 500

    @jwt_required()
    def put(self, service_id):
        """Update an existing service. Only admins can update services."""
        try:
            identity = get_jwt_identity()
            user = User.query.get(identity)
            
            if not user or user.role != UserRole.ADMIN:
                return {"message": "Only admins can update services"}, 403

            service = Service.query.get(service_id)
            if not service:
                return {"error": "Service not found"}, 404

            data = request.get_json()
            if not data:
                return {"error": "No data provided"}, 400

            # Update category if provided
            if "category" in data:
                try:
                    category_enum = ServiceCategory[data['category'].upper()]
                    service.category = category_enum
                except KeyError:
                    return {
                        "error": f"Invalid category. Must be one of: {', '.join([c.value for c in ServiceCategory])}"
                    }, 400

            # Update title and regenerate slug if title changed
            if "title" in data:
                service.title = data['title']
                if 'slug' not in data:
                    new_slug = slugify(data['title'])
                    # Check if new slug conflicts with another service
                    existing = Service.query.filter(
                        Service.slug == new_slug,
                        Service.id != service_id
                    ).first()
                    if not existing:
                        service.slug = new_slug
            
            # Update slug if explicitly provided
            if "slug" in data:
                # Check if slug conflicts with another service
                existing = Service.query.filter(
                    Service.slug == data['slug'],
                    Service.id != service_id
                ).first()
                if existing:
                    return {"error": "Slug already exists"}, 400
                service.slug = data['slug']
            
            if "description" in data:
                service.description = data.get("description")
            
            if "price_min" in data:
                if data['price_min'] is not None:
                    try:
                        price_min = Decimal(str(data["price_min"]))
                        if price_min < 0:
                            return {"error": "Price minimum cannot be negative"}, 400
                        service.price_min = price_min
                    except (ValueError, TypeError):
                        return {"error": "Invalid price_min format"}, 400
                else:
                    service.price_min = None
            
            if "price_max" in data:
                if data['price_max'] is not None:
                    try:
                        price_max = Decimal(str(data["price_max"]))
                        if price_max < 0:
                            return {"error": "Price maximum cannot be negative"}, 400
                        service.price_max = price_max
                    except (ValueError, TypeError):
                        return {"error": "Invalid price_max format"}, 400
                else:
                    service.price_max = None
            
            # Validate price range
            if service.price_min and service.price_max and service.price_min > service.price_max:
                return {"error": "price_min cannot be greater than price_max"}, 400
            
            if "price_display" in data:
                service.price_display = data["price_display"]
            
            if "features" in data:
                service.features = data["features"]
            
            if "is_active" in data:
                service.is_active = bool(data["is_active"])
            
            if "is_featured" in data:
                service.is_featured = bool(data["is_featured"])
            
            if "display_order" in data:
                try:
                    display_order = int(data["display_order"])
                    service.display_order = display_order
                except (ValueError, TypeError):
                    return {"error": "Invalid display_order format"}, 400
            
            if "icon_name" in data:
                service.icon_name = data["icon_name"]

            # Update the updated_at timestamp
            service.updated_at = datetime.utcnow()

            db.session.commit()
            
            logger.info(f"Service updated by admin {user.email}: {service.title}")
            
            return {"message": "Service updated successfully", "service": service.as_dict()}, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating service: {str(e)}")
            return {"error": f"An error occurred: {str(e)}"}, 500

    @jwt_required()
    def delete(self, service_id):
        """Delete a service (Only admins can delete services)."""
        try:
            identity = get_jwt_identity()
            user = User.query.get(identity)
            
            if not user or user.role != UserRole.ADMIN:
                return {"message": "Only admins can delete services"}, 403

            service = Service.query.get(service_id)
            if not service:
                return {"error": "Service not found"}, 404

            service_title = service.title
            
            db.session.delete(service)
            db.session.commit()
            
            logger.info(f"Service deleted by admin {user.email}: {service_title}")
            
            return {"message": "Service deleted successfully"}, 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting service id {service_id}: {str(e)}", exc_info=True)
            return {"error": "An unexpected error occurred during service deletion."}, 500


class ServiceBySlugResource(Resource):
    """Resource for retrieving services by slug."""
    
    def get(self, slug):
        """Get a single service by slug (PUBLIC)"""
        try:
            service = Service.query.filter_by(slug=slug, is_active=True).first()
            
            if not service:
                return {"message": "Service not found"}, 404
            
            return service.as_dict(), 200
            
        except Exception as e:
            logger.error(f"Error fetching service {slug}: {str(e)}")
            return {"message": "Error fetching service"}, 500


class ServiceCategoryResource(Resource):
    """Resource for handling service categories."""
    
    def get(self):
        """Get all service categories (PUBLIC)"""
        try:
            categories = [
                {
                    "name": category.name,
                    "value": category.value
                }
                for category in ServiceCategory
            ]
            
            return {"categories": categories}, 200
            
        except Exception as e:
            logger.error(f"Error fetching categories: {str(e)}")
            return {"message": "Error fetching categories"}, 500


class FeaturedServicesResource(Resource):
    """Resource for handling featured services."""
    
    def get(self):
        """Get all featured services (PUBLIC)"""
        try:
            services = Service.query.filter_by(
                is_active=True,
                is_featured=True
            ).order_by(Service.display_order.asc()).all()
            
            return {
                'services': [service.as_dict() for service in services],
                'total': len(services)
            }, 200
            
        except Exception as e:
            logger.error(f"Error fetching featured services: {str(e)}")
            return {"message": "Error fetching featured services"}, 500


class AdminServicesResource(Resource):
    """Resource for admins to manage all services."""
    
    @jwt_required()
    def get(self):
        """Retrieve all services for admin management (including inactive ones)."""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)

            if not user or user.role != UserRole.ADMIN:
                return {"message": "Only admins can access this endpoint"}, 403

            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            # Get all services (including inactive ones) with pagination
            services = Service.query.order_by(
                Service.display_order.asc(),
                Service.created_at.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)
            
            return {
                'services': [service.as_dict() for service in services.items],
                'total': services.total,
                'pages': services.pages,
                'current_page': services.page
            }, 200
            
        except Exception as e:
            logger.error(f"Error fetching admin services: {str(e)}")
            return {"message": "Error fetching services"}, 500


def register_service_resources(api):
    """Registers the ServiceResource routes with Flask-RESTful API."""
    api.add_resource(ServiceResource, "/services", "/services/<int:service_id>")
    api.add_resource(ServiceBySlugResource, "/services/slug/<string:slug>")
    api.add_resource(ServiceCategoryResource, "/service-categories")
    api.add_resource(FeaturedServicesResource, "/services/featured")
    api.add_resource(AdminServicesResource, "/admin/services")