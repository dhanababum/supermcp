import requests
from api.config import LogoStorageType, settings
import os
from starlette.responses import FileResponse
from PIL import Image
from io import BytesIO


def store_logo(source_logo_url: str, name: str):
    if not source_logo_url or source_logo_url.strip() == "":
        return None
        
    if settings.LOGO_STORAGE_TYPE == LogoStorageType.FILESYSTEM:
        try:
            # Create directory if it doesn't exist
            os.makedirs(settings.LOGO_STORAGE_PATH, exist_ok=True)
            
            # Get the image from URL
            response = requests.get(source_logo_url, stream=True, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes

            # Open the image from the raw content of the response
            img = Image.open(BytesIO(response.content))
            
            # Determine file extension from image format
            if img.format:
                file_extension = img.format.lower()
            else:
                # Fallback to PNG if format is unknown
                file_extension = 'png'
            
            # Create filename with proper extension
            filename = f"{name}.{file_extension}"
            filepath = os.path.join(settings.LOGO_STORAGE_PATH, filename)
            
            # Save the image
            img.save(filepath)
            img.close()
            return filepath
            
        except Exception as e:
            print(f"Warning: Failed to store logo for {name}: {str(e)}")
            return None


def get_logo(name: str):
    if settings.LOGO_STORAGE_TYPE == LogoStorageType.FILESYSTEM:
        return FileResponse(os.path.join(settings.LOGO_STORAGE_PATH, name))
    else:
        raise ValueError(f"Invalid logo storage type: {settings.LOGO_STORAGE_TYPE}")