# app/services/cloudinary_service.py

import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
import logging
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

logger = logging.getLogger(__name__)

# Initialize Cloudinary configuration
def get_cloudinary_config():
    """Get Cloudinary configuration from environment variables"""
    return {
        'cloud_name': os.environ.get('CLOUDINARY_CLOUD_NAME'),
        'api_key': os.environ.get('CLOUDINARY_API_KEY'),
        'api_secret': os.environ.get('CLOUDINARY_API_SECRET'),
        'upload_folder': os.environ.get('CLOUDINARY_UPLOAD_FOLDER', 'lenny_media'),
        'allowed_formats': {'jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'mov', 'avi', 'mkv'},
        'max_file_size': 100 * 1024 * 1024,  # 100MB
        'secure': True
    }

# Initialize Cloudinary
config = get_cloudinary_config()
cloudinary.config(
    cloud_name=config['cloud_name'],
    api_key=config['api_key'],
    api_secret=config['api_secret'],
    secure=config['secure']
)

def validate_file(file, file_type='image'):
    """Validate file before upload"""
    try:
        # Get file extension
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        # Check if file type is allowed
        if file_ext not in config['allowed_formats']:
            return False, f"File format '{file_ext}' not allowed. Allowed formats: {', '.join(config['allowed_formats'])}", None, None
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > config['max_file_size']:
            max_size_mb = config['max_file_size'] // (1024 * 1024)
            return False, f"File size exceeds {max_size_mb}MB limit", None, None
        
        return True, None, file_size, file_ext
        
    except Exception as e:
        logger.error(f"Error validating file: {str(e)}")
        return False, f"Error validating file: {str(e)}", None, None

def upload_profile_picture(file, user_id, user_name):
    """Upload profile picture to Cloudinary with unique public_id"""
    try:
        # Generate unique public_id with timestamp
        timestamp = int(datetime.utcnow().timestamp())
        unique_id = str(uuid.uuid4())[:8]  # Get first 8 chars of UUID
        clean_name = user_name.replace(' ', '_').lower()
        
        # Generate unique public_id with timestamp and unique_id
        base_name = f"{clean_name}_{timestamp}_{unique_id}"
        public_id = f"{config['upload_folder']}/profiles/user_{user_id}/{base_name}"
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            file,
            public_id=public_id,
            folder=f"{config['upload_folder']}/profiles/user_{user_id}",
            overwrite=False,  # Don't overwrite, create new file
            resource_type="auto",
            transformation=[
                {'width': 400, 'height': 400, 'crop': 'thumb', 'gravity': 'face'},
                {'quality': 'auto:good'},
                {'fetch_format': 'auto'}
            ],
            tags=[f'user_{user_id}', 'profile', 'avatar']
        )
        
        # Generate optimized avatar URL
        avatar_url = cloudinary.CloudinaryImage(upload_result['public_id']).build_url(
            width=200,
            height=200,
            crop='thumb',
            gravity='face',
            quality='auto:good',
            fetch_format='auto'
        )
        
        # Generate thumbnail URL
        thumbnail_url = cloudinary.CloudinaryImage(upload_result['public_id']).build_url(
            width=100,
            height=100,
            crop='thumb',
            quality='auto:good',
            fetch_format='auto'
        )
        
        logger.info(f"Profile picture uploaded: {upload_result['public_id']}")
        
        return {
            'success': True,
            'public_id': upload_result['public_id'],
            'original_url': upload_result['secure_url'],
            'avatar_url': avatar_url,
            'thumbnail_url': thumbnail_url,
            'width': upload_result.get('width'),
            'height': upload_result.get('height'),
            'format': upload_result.get('format'),
            'resource_type': upload_result.get('resource_type'),
            'created_at': upload_result.get('created_at'),
            'bytes': upload_result.get('bytes'),
            'version': upload_result.get('version')
        }
        
    except Exception as e:
        logger.error(f"Error uploading profile picture: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to upload profile picture'
        }

def cleanup_old_profile_picture(public_id):
    """Clean up old profile picture from Cloudinary"""
    try:
        if not public_id:
            return None
        
        # Extract base folder and filename
        parts = public_id.split('/')
        if len(parts) >= 3:
            user_folder = '/'.join(parts[:-1])  # Get folder path without filename
            filename_prefix = parts[-1].split('_')[0]  # Get name part before timestamp
            
            # List all resources in the user's profile folder
            resources = cloudinary.api.resources(
                type='upload',
                prefix=user_folder,
                max_results=50
            )
            
            # Keep only the 5 most recent profile pictures
            if resources.get('resources'):
                # Filter for this user's profile pictures
                profile_pics = []
                for resource in resources['resources']:
                    resource_name = resource['public_id'].split('/')[-1]
                    if filename_prefix in resource_name:
                        profile_pics.append(resource)
                
                # Sort by creation time (newest first)
                profile_pics.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                
                # Delete old ones (keep only 5 most recent)
                for old_pic in profile_pics[5:]:
                    try:
                        delete_result = cloudinary.uploader.destroy(old_pic['public_id'])
                        if delete_result.get('result') == 'ok':
                            logger.info(f"Cleaned up old profile picture: {old_pic['public_id']}")
                    except Exception as e:
                        logger.warning(f"Failed to delete old profile picture {old_pic['public_id']}: {str(e)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error cleaning up old profile pictures: {str(e)}")
        return False

def delete_image(public_id):
    """Delete image from Cloudinary"""
    try:
        result = cloudinary.uploader.destroy(public_id)
        
        if result.get('result') == 'ok':
            logger.info(f"Image deleted from Cloudinary: {public_id}")
            return {'success': True, 'result': result}
        else:
            logger.warning(f"Failed to delete image {public_id}: {result}")
            return {'success': False, 'error': result.get('result'), 'result': result}
            
    except Exception as e:
        logger.error(f"Error deleting image from Cloudinary: {str(e)}")
        return {'success': False, 'error': str(e)}

def generate_cloudinary_url(public_id, **kwargs):
    """Generate Cloudinary URL with transformations"""
    try:
        if not public_id:
            return None
        
        # Get transformation parameters
        width = kwargs.get('width')
        height = kwargs.get('height')
        crop = kwargs.get('crop')
        gravity = kwargs.get('gravity')
        quality = kwargs.get('quality', 'auto:good')
        fetch_format = kwargs.get('fetch_format', 'auto')
        
        # Build transformations
        transformations = []
        
        if width or height:
            if crop == 'thumb':
                transformations.append({
                    'width': width,
                    'height': height,
                    'crop': 'thumb',
                    'gravity': gravity or 'face'
                })
            else:
                transformations.append({
                    'width': width,
                    'height': height,
                    'crop': crop or 'fill'
                })
        
        transformations.append({'quality': quality})
        transformations.append({'fetch_format': fetch_format})
        
        # Generate URL with cache-busting timestamp
        timestamp = int(datetime.utcnow().timestamp())
        
        # Build the URL
        url = cloudinary.CloudinaryImage(public_id).build_url(
            transformation=transformations,
            secure=True
        )
        
        # Add cache-busting parameter
        url = f"{url}?_={timestamp}"
        
        return url
        
    except Exception as e:
        logger.error(f"Error generating Cloudinary URL: {str(e)}")
        return None

def extract_public_id_from_url(url):
    """Extract public_id from Cloudinary URL"""
    try:
        if not url or 'cloudinary.com' not in url:
            return None
        
        # Parse the URL to extract public_id
        parts = url.split('/')
        
        # Find the index after 'upload'
        try:
            upload_index = parts.index('upload')
            # The public_id is everything after the version (v1234567890)
            for i, part in enumerate(parts[upload_index + 1:], upload_index + 1):
                if part.startswith('v'):
                    # Join all parts after the version
                    public_id_parts = parts[i + 1:]
                    return '/'.join(public_id_parts)
        except ValueError:
            pass
        
        # Alternative pattern matching
        import re
        patterns = [
            r'/(v\d+/[^?]+)',  # Pattern with version
            r'/upload/([^?]+)',  # Pattern without version
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
        
    except Exception as e:
        logger.error(f"Error extracting public_id from URL: {str(e)}")
        return None

def test_cloudinary_connection():
    """Test Cloudinary connection"""
    try:
        # Try to ping Cloudinary
        cloudinary.api.ping()
        return {'success': True, 'message': 'Cloudinary connection successful'}
    except Exception as e:
        logger.error(f"Cloudinary connection test failed: {str(e)}")
        return {'success': False, 'error': str(e)}

def upload_image(file, folder=None, public_id=None, transformations=None):
    """Upload an image to Cloudinary"""
    try:
        upload_options = {
            'resource_type': 'image',
            'overwrite': False
        }
        
        if folder:
            upload_options['folder'] = folder
        if public_id:
            upload_options['public_id'] = public_id
        if transformations:
            upload_options['transformation'] = transformations
        
        upload_result = cloudinary.uploader.upload(file, **upload_options)
        
        return {
            'success': True,
            'public_id': upload_result['public_id'],
            'url': upload_result['secure_url'],
            'width': upload_result.get('width'),
            'height': upload_result.get('height'),
            'format': upload_result.get('format')
        }
        
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        return {'success': False, 'error': str(e)}

def upload_file(file, file_type='image', folder=None, public_id=None, transformations=None):
    """Upload any file to Cloudinary"""
    try:
        upload_options = {
            'resource_type': 'auto',
            'overwrite': False
        }
        
        if folder:
            upload_options['folder'] = folder
        if public_id:
            upload_options['public_id'] = public_id
        if transformations:
            upload_options['transformation'] = transformations
        
        upload_result = cloudinary.uploader.upload(file, **upload_options)
        
        return {
            'success': True,
            'public_id': upload_result['public_id'],
            'url': upload_result['secure_url'],
            'resource_type': upload_result['resource_type'],
            'format': upload_result.get('format'),
            'bytes': upload_result.get('bytes')
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return {'success': False, 'error': str(e)}

def upload_portfolio_image(file, portfolio_id, title, category):
    """Upload portfolio image to Cloudinary"""
    try:
        clean_title = title.replace(' ', '_').lower()[:50]
        public_id = f"{config['upload_folder']}/portfolios/{portfolio_id}/{clean_title}"
        
        upload_result = cloudinary.uploader.upload(
            file,
            public_id=public_id,
            folder=f"{config['upload_folder']}/portfolios/{portfolio_id}",
            resource_type="auto",
            tags=[f'portfolio_{portfolio_id}', category, 'portfolio']
        )
        
        return {
            'success': True,
            'public_id': upload_result['public_id'],
            'url': upload_result['secure_url'],
            'thumbnail_url': cloudinary.CloudinaryImage(upload_result['public_id']).build_url(
                width=300,
                height=200,
                crop='fill',
                quality='auto:good'
            )
        }
        
    except Exception as e:
        logger.error(f"Error uploading portfolio image: {str(e)}")
        return {'success': False, 'error': str(e)}

def upload_service_image(file, service_id, service_name):
    """Upload service image to Cloudinary"""
    try:
        clean_name = service_name.replace(' ', '_').lower()
        public_id = f"{config['upload_folder']}/services/{service_id}/{clean_name}"
        
        upload_result = cloudinary.uploader.upload(
            file,
            public_id=public_id,
            folder=f"{config['upload_folder']}/services/{service_id}",
            resource_type="auto",
            tags=[f'service_{service_id}', 'service']
        )
        
        return {
            'success': True,
            'public_id': upload_result['public_id'],
            'url': upload_result['secure_url'],
            'thumbnail_url': cloudinary.CloudinaryImage(upload_result['public_id']).build_url(
                width=300,
                height=200,
                crop='fill',
                quality='auto:good'
            )
        }
        
    except Exception as e:
        logger.error(f"Error uploading service image: {str(e)}")
        return {'success': False, 'error': str(e)}