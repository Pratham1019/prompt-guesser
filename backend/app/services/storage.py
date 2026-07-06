import asyncio
import os
import re
from datetime import date
from typing import Optional

import cloudinary
import cloudinary.uploader

from app.config import settings
from app.logging import logger


class StorageError(Exception):
    """Base exception for storage errors."""

    pass


class StorageService:
    """
    Storage service supporting both local disk storage and Cloudinary cloud storage.
    """

    def __init__(self) -> None:
        self.provider = settings.IMAGE_STORAGE_PROVIDER.lower()

        if self.provider == "cloudinary":
            if not all(
                [
                    settings.CLOUDINARY_CLOUD_NAME,
                    settings.CLOUDINARY_API_KEY,
                    settings.CLOUDINARY_API_SECRET,
                ]
            ):
                raise StorageError("Cloudinary configuration settings are missing in settings.")

            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET,
                secure=True,
            )
            logger.info("Initialized Cloudinary StorageService.")
        else:
            self.local_dir = settings.STORAGE_LOCAL_DIR
            os.makedirs(self.local_dir, exist_ok=True)
            logger.info(f"Initialized Local StorageService pointing to directory: {self.local_dir}")

    @staticmethod
    def get_filename(target_date: date, extension: str = "jpg") -> str:
        """Returns the standard filename for a challenge."""
        return f"{target_date.strftime('%Y-%m-%d')}.{extension}"

    @staticmethod
    def get_storage_path(target_date: date, extension: str = "jpg") -> str:
        """Returns the local storage relative path for the challenge."""
        return f"{target_date.strftime('%Y-%m-%d')}.{extension}"

    async def upload_image(
        self, image_bytes: bytes, target_date: Optional[date] = None, extension: str = "jpg"
    ) -> str:
        """
        Saves the image bytes to local storage or Cloudinary, returning the public access path/URL.
        """
        if not target_date:
            target_date = date.today()

        filename = self.get_filename(target_date, extension)
        loop = asyncio.get_running_loop()

        # CLOUDINARY UPLOAD WORKFLOW
        if self.provider == "cloudinary":
            # Cloudinary public ID without the extension
            public_id = f"prompt_guesser/{target_date.strftime('%Y-%m-%d')}"

            try:

                def _upload_to_cloudinary():
                    return cloudinary.uploader.upload(
                        image_bytes,
                        public_id=public_id,
                        overwrite=True,
                        resource_type="image",
                    )

                logger.info(f"Uploading image to Cloudinary: {public_id}")
                res = await loop.run_in_executor(None, _upload_to_cloudinary)
                secure_url = res.get("secure_url")

                if not secure_url:
                    raise StorageError("Cloudinary response did not contain secure_url.")

                logger.info(f"Image uploaded to Cloudinary successfully: {secure_url}")
                return secure_url

            except Exception as e:
                logger.error(f"Cloudinary upload failed: {e}")
                raise StorageError(f"Cloudinary upload failed: {e}") from e

        # LOCAL STORAGE WORKFLOW
        else:
            filepath = os.path.join(self.local_dir, filename)
            try:

                def _write_local():
                    with open(filepath, "wb") as f:
                        f.write(image_bytes)

                await loop.run_in_executor(None, _write_local)
                logger.info(f"Image stored locally successfully: {filename}")
                return f"/storage/images/{filename}"

            except Exception as e:
                logger.error(f"Local storage upload failed: {e}")
                raise StorageError(f"Local upload failed: {e}") from e

    async def delete_image(self, storage_path: str) -> None:
        """
        Deletes the image file from local storage or Cloudinary.
        """
        loop = asyncio.get_running_loop()

        # CLOUDINARY DELETE WORKFLOW
        if self.provider == "cloudinary":
            # Extract public_id (e.g. prompt_guesser/2026-07-06) from the secure URL
            match = re.search(r"(prompt_guesser/[^./?]+)", storage_path)
            if not match:
                logger.warning(
                    f"Could not parse Cloudinary public_id from path: {storage_path}. Skipping deletion."
                )
                return

            public_id = match.group(1)

            try:

                def _delete_from_cloudinary():
                    return cloudinary.uploader.destroy(public_id)

                logger.info(f"Deleting image from Cloudinary: {public_id}")
                res = await loop.run_in_executor(None, _delete_from_cloudinary)
                result_status = res.get("result")

                logger.info(f"Cloudinary deletion result: {result_status} for {public_id}")

            except Exception as e:
                logger.error(f"Cloudinary deletion failed: {e}")
                raise StorageError(f"Cloudinary deletion failed: {e}") from e

        # LOCAL STORAGE DELETE WORKFLOW
        else:
            filename = os.path.basename(storage_path)
            filepath = os.path.join(self.local_dir, filename)
            if os.path.exists(filepath):
                try:

                    def _remove_local():
                        os.remove(filepath)

                    await loop.run_in_executor(None, _remove_local)
                    logger.info(f"Deleted local image: {filename}")
                except Exception as e:
                    logger.error(f"Failed to delete local image {filepath}: {e}")
                    raise StorageError(f"Local deletion failed: {e}") from e
