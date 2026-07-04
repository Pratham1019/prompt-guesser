import os
import uuid

import aiofiles

from app.config import settings
from app.logging import logger


class StorageError(Exception):
    """Base exception for storage errors."""

    pass


class StorageService:
    """
    Storage abstraction layer.
    Currently implements local filesystem storage, designed to be easily swapped with Supabase Storage.
    """

    def __init__(self) -> None:
        self.local_dir = settings.STORAGE_LOCAL_DIR
        os.makedirs(self.local_dir, exist_ok=True)

    async def upload_image(self, image_bytes: bytes, extension: str = "jpg") -> str:
        """
        Uploads an image and returns its accessible URL or identifier.
        """
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.{extension}"
        filepath = os.path.join(self.local_dir, filename)

        try:
            async with aiofiles.open(filepath, "wb") as f:
                await f.write(image_bytes)

            logger.info(f"Image uploaded successfully: {filename}")

            # Return a relative URL or identifier that the frontend can use
            # In Supabase, this would return the public URL.
            return f"/storage/images/{filename}"
        except Exception as e:
            logger.error(f"Failed to upload image {filename}: {e}")
            raise StorageError(f"Upload failed: {e}") from e

    async def delete_image(self, image_url: str) -> None:
        """
        Deletes an image from storage.
        """
        filename = os.path.basename(image_url)
        filepath = os.path.join(self.local_dir, filename)
        try:
            # Check if file exists, then delete in an async-friendly way
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Image deleted successfully from storage: {filename}")
        except Exception as e:
            logger.error(f"Failed to delete image {filename}: {e}")
            raise StorageError(f"Delete failed: {e}") from e
