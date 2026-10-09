import asyncio
import io
import uuid
from pathlib import Path
from typing import Literal

import boto3
from botocore.config import Config
from fastapi import UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

from cashevide_api.config import settings


class ImageError(Exception):
    status_code: int = 422


class InvalidImageError(ImageError):
    status_code = 422


class ImageTooLargeError(ImageError):
    status_code = 413


def _s3():
    return boto3.client(
        "s3",
        endpoint_url=settings.aws_s3_endpoint_url,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def process_image(
    data: bytes, fmt: Literal["jpg", "png"], max_size: int = 512
) -> tuple[bytes, str]:
    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)
        img.load()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as exc:
        raise InvalidImageError(
            "Upload a valid image. The file you uploaded was either not an "
            "image or a corrupted image."
        ) from exc

    if fmt == "jpg":
        if img.mode != "RGB":
            img = img.convert("RGB")
        options, content_type = {"format": "JPEG", "quality": 85}, "image/jpeg"
    else:
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        options, content_type = {"format": "PNG", "optimize": True}, "image/png"

    img.thumbnail((max_size, max_size))

    buffer = io.BytesIO()
    img.save(buffer, **options)
    return buffer.getvalue(), content_type


def _save_sync(key: str, data: bytes, content_type: str) -> None:
    if settings.use_s3_storage:
        _s3().put_object(
            Bucket=settings.aws_storage_bucket_name,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
    else:
        path = Path(settings.media_root) / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def _delete_sync(key: str) -> None:
    if settings.use_s3_storage:
        _s3().delete_object(Bucket=settings.aws_storage_bucket_name, Key=key)
    else:
        (Path(settings.media_root) / key).unlink(missing_ok=True)


async def save_image(
    upload: UploadFile,
    folder: str,
    fmt: Literal["jpg", "png"],
    max_size: int = 512,
) -> str:
    max_bytes = settings.max_image_upload_mb * 1024 * 1024
    data = await upload.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ImageTooLargeError(
            f"Image is too large. Maximum size is {settings.max_image_upload_mb} MB."
        )
    processed, content_type = await asyncio.to_thread(
        process_image, data, fmt, max_size
    )
    key = f"{folder}/{uuid.uuid4().hex}.{fmt}"
    await asyncio.to_thread(_save_sync, key, processed, content_type)
    return key


async def delete_image(key: str | None) -> None:
    if key:
        await asyncio.to_thread(_delete_sync, key)


def media_url(key: str | None) -> str | None:
    if not key:
        return None
    if settings.use_s3_storage:
        return f"https://{settings.aws_s3_custom_domain}/{key}"
    return f"{settings.media_base_url}{key}"
