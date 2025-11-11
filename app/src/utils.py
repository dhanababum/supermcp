import asyncio
import httpx
import os
from starlette.responses import FileResponse
from PIL import Image
from io import BytesIO

from src.config import LogoStorageType, settings


async def store_logo(source_logo_url: str, target_logo_path: str, name: str):
    if not source_logo_url or source_logo_url.strip() == "":
        return None

    if settings.LOGO_STORAGE_TYPE == LogoStorageType.FILESYSTEM:
        try:
            # Create directory if it doesn't exist
            os.makedirs(target_logo_path, exist_ok=True)

            # Get the image from URL
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    source_logo_url, timeout=10)
                image = await asyncio.to_thread(
                    Image.open, BytesIO(await response.aread()))
                # Determine file extension from image format
                if image.format:
                    file_extension = image.format.lower()
                else:
                    # Fallback to PNG if format is unknown
                    file_extension = "png"
                # Create filename with proper extension
                filename = f"{name}.{file_extension}"
                filepath = os.path.join(target_logo_path, filename)
                await asyncio.to_thread(image.save, filepath)
                return filename

        except Exception as e:
            print(f"Warning: Failed to store logo for {name}: {str(e)}")
            return None


async def get_logo(target_logo_path: str, name: str):
    if settings.LOGO_STORAGE_TYPE == LogoStorageType.FILESYSTEM:
        filepath = os.path.join(target_logo_path, name)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Logo file not found: {filepath}")
        return await asyncio.to_thread(
            FileResponse, filepath)
    else:
        raise ValueError(
            f"Invalid logo storage type: {target_logo_path}") from None


def get_tool_id(name: str):
    return name.replace("_", "-")
