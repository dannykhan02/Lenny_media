"""
Helper functions for QuoteRequest service handling with pricing
"""

import logging
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def enrich_selected_services(service_ids: List, db_session: Session) -> List[Dict]:
    """
    Enrich service IDs with full service information including pricing
    
    Args:
        service_ids: List of service IDs, service objects, or mixed formats
        db_session: Database session
        
    Returns:
        List of service dictionaries with complete pricing information
    """
    from app.models.service import Service
    
    enriched_services = []
    
    for item in service_ids:
        # Handle multiple input formats:
        # 1. Plain integer: 3
        # 2. Dict with 'service_id': {"service_id": 3}
        # 3. Dict with 'id': {"id": 3, "title": "Wedding"}
        # 4. Already enriched service dict (with price_min/price_max)
        
        if isinstance(item, int):
            service_id = item
        elif isinstance(item, dict):
            # Check if already enriched (has price_min or price_max)
            if item.get('price_min') is not None or item.get('price_max') is not None:
                # Already enriched, keep as is but ensure all fields
                enriched_service = {
                    "service_id": item.get('service_id') or item.get('id'),
                    "id": item.get('service_id') or item.get('id'),
                    "title": item.get('title'),
                    "category": item.get('category'),
                    "price_min": item.get('price_min'),
                    "price_max": item.get('price_max'),
                    "price_display": item.get('price_display'),
                    "features": item.get('features') or [],
                    "price_range": item.get('price_range')
                }
                # Ensure price_range exists
                if not enriched_service.get('price_range') and enriched_service.get('price_min') and enriched_service.get('price_max'):
                    enriched_service['price_range'] = f"Ksh {enriched_service['price_min']:,.0f} – {enriched_service['price_max']:,.0f}"
                enriched_services.append(enriched_service)
                continue
            
            # Not enriched yet, extract service_id
            service_id = item.get('service_id') or item.get('id')
        else:
            continue
        
        if not service_id:
            continue
            
        service = db_session.query(Service).filter_by(
            id=service_id, 
            is_active=True
        ).first()
        
        if service:
            # Calculate price_range if not provided
            price_range = service.price_display
            if not price_range and service.price_min and service.price_max:
                price_range = f"Ksh {service.price_min:,.0f} – {service.price_max:,.0f}"
            
            enriched_services.append({
                "service_id": service.id,
                "id": service.id,  # Include both for compatibility
                "title": service.title,
                "category": service.category.value if hasattr(service.category, 'value') else service.category,
                "price_min": float(service.price_min) if service.price_min else None,
                "price_max": float(service.price_max) if service.price_max else None,
                "price_display": service.price_display,
                "price_range": price_range,
                "features": service.features or []
            })
    
    return enriched_services


def validate_service_selection(selected_services, db_session: Session) -> Tuple[bool, Optional[str]]:
    """
    Validate selected services format and existence
    
    Returns:
        (is_valid, error_message)
    """
    from app.models.service import Service
    
    if not isinstance(selected_services, list):
        return False, "selected_services must be an array"
    
    if len(selected_services) == 0:
        return False, "At least one service must be selected"
    
    # Support multiple formats:
    # [1, 2, 3] or [{"service_id": 1}, {"id": 2, "title": "..."}, ...]
    for item in selected_services:
        if isinstance(item, int):
            service_id = item
        elif isinstance(item, dict):
            # Try 'service_id' first, then fall back to 'id'
            service_id = item.get("service_id") or item.get("id")
            if not service_id:
                return False, "Service object must contain 'service_id' or 'id' field"
        else:
            return False, "Invalid service format. Use service IDs or service objects"
        
        # Check if service exists and is active
        service = db_session.query(Service).filter_by(
            id=service_id, 
            is_active=True
        ).first()
        
        if not service:
            return False, f"Service with ID {service_id} not found or inactive"
    
    return True, None


def calculate_price_estimate(selected_services: List[Dict]) -> Dict:
    """
    Calculate estimated price range from selected services
    
    Args:
        selected_services: List of enriched service dictionaries
        
    Returns:
        {
            "min_estimate": 130000.00,
            "max_estimate": 350000.00,
            "formatted": "Ksh 130,000 – 350,000",
            "service_count": 2
        }
    """
    if not selected_services:
        return {
            "min_estimate": None,
            "max_estimate": None,
            "formatted": "Price on request",
            "service_count": 0
        }
    
    total_min = Decimal('0')
    total_max = Decimal('0')
    service_count = 0
    
    for service in selected_services:
        # Check if service has pricing information
        price_min = service.get('price_min')
        price_max = service.get('price_max')
        
        if price_min is not None:
            try:
                total_min += Decimal(str(price_min))
                service_count += 1
            except Exception as e:
                logger.warning(f"Error processing price_min for service {service.get('id')}: {str(e)}")
        
        if price_max is not None:
            try:
                total_max += Decimal(str(price_max))
            except Exception as e:
                logger.warning(f"Error processing price_max for service {service.get('id')}: {str(e)}")
    
    # If we have some prices but not all, handle gracefully
    if total_min == 0 and total_max == 0:
        # Check if any services have partial pricing
        has_partial_pricing = any(
            s.get('price_min') or s.get('price_max') 
            for s in selected_services
        )
        
        if has_partial_pricing:
            # Try to calculate based on available prices
            available_min = Decimal('0')
            available_max = Decimal('0')
            min_count = 0
            max_count = 0
            
            for service in selected_services:
                if service.get('price_min'):
                    available_min += Decimal(str(service['price_min']))
                    min_count += 1
                if service.get('price_max'):
                    available_max += Decimal(str(service['price_max']))
                    max_count += 1
            
            if min_count > 0 and max_count > 0:
                # Estimate by averaging available prices
                avg_min_price = available_min / min_count
                avg_max_price = available_max / max_count
                estimated_min = avg_min_price * len(selected_services)
                estimated_max = avg_max_price * len(selected_services)
                
                return {
                    "min_estimate": float(estimated_min),
                    "max_estimate": float(estimated_max),
                    "formatted": f"Ksh {estimated_min:,.0f} – {estimated_max:,.0f} (estimated)",
                    "service_count": len(selected_services),
                    "estimated": True
                }
        
        return {
            "min_estimate": None,
            "max_estimate": None,
            "formatted": "Price on request",
            "service_count": len(selected_services)
        }
    
    # Format the price range
    formatted_range = f"Ksh {total_min:,.0f} – {total_max:,.0f}"
    
    return {
        "min_estimate": float(total_min),
        "max_estimate": float(total_max),
        "formatted": formatted_range,
        "service_count": service_count
    }


def get_services_by_category(selected_services: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group selected services by category for better display
    
    Returns:
        {
            "photography": [...],
            "videography": [...]
        }
    """
    categorized = {}
    
    for service in selected_services:
        category = service.get('category', 'other')
        if category not in categorized:
            categorized[category] = []
        categorized[category].append(service)
    
    return categorized


def re_enrich_services_if_needed(selected_services: List[Dict], db_session: Session) -> List[Dict]:
    """
    Check if services need re-enrichment and re-enrich if needed
    
    Args:
        selected_services: Current selected services
        db_session: Database session
        
    Returns:
        Re-enriched services if needed, otherwise original services
    """
    if not selected_services:
        return selected_services
    
    # Check if first service has pricing info
    first_service = selected_services[0]
    if first_service.get('price_min') is None and first_service.get('price_max') is None:
        # Services need re-enrichment
        logger.info("Services need re-enrichment, enriching now...")
        return enrich_selected_services(selected_services, db_session)
    
    return selected_services