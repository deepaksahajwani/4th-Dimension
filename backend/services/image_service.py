"""
Image Processing Service
Handles thumbnail generation and image optimization
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, Tuple
import logging
from PIL import Image

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("/app/uploads")
THUMBNAIL_DIR = UPLOAD_DIR / "thumbnails"
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

# Thumbnail sizes
THUMBNAIL_SIZES = {
    "small": (150, 150),
    "medium": (300, 300),
    "large": (600, 600)
}

# Max file size for processing (10MB)
MAX_PROCESS_SIZE = 10 * 1024 * 1024


async def generate_thumbnail(
    source_path: str,
    size: str = "medium",
    quality: int = 85
) -> Optional[str]:
    """
    Generate a thumbnail for an image file
    Returns the path to the thumbnail or None if failed
    """
    try:
        source = Path(source_path)
        if not source.exists():
            logger.warning(f"Source file not found: {source_path}")
            return None
        
        # Check file size
        if source.stat().st_size > MAX_PROCESS_SIZE:
            logger.warning(f"File too large for thumbnail: {source_path}")
            return None
        
        # Get thumbnail dimensions
        dimensions = THUMBNAIL_SIZES.get(size, THUMBNAIL_SIZES["medium"])
        
        # Generate thumbnail filename
        thumb_name = f"{source.stem}_{size}{source.suffix}"
        thumb_path = THUMBNAIL_DIR / thumb_name
        
        # Process in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            _create_thumbnail,
            str(source),
            str(thumb_path),
            dimensions,
            quality
        )
        
        if thumb_path.exists():
            return f"/api/uploads/thumbnails/{thumb_name}"
        
        return None
        
    except Exception as e:
        logger.error(f"Error generating thumbnail: {e}")
        return None


def _create_thumbnail(
    source_path: str,
    dest_path: str,
    dimensions: Tuple[int, int],
    quality: int
):
    """Synchronous thumbnail creation (runs in thread pool)"""
    try:
        with Image.open(source_path) as img:
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Calculate aspect ratio preserving resize
            img.thumbnail(dimensions, Image.Resampling.LANCZOS)
            
            # Save with optimization
            img.save(
                dest_path,
                quality=quality,
                optimize=True
            )
            
            logger.info(f"Thumbnail created: {dest_path}")
            
    except Exception as e:
        logger.error(f"Thumbnail creation error: {e}")
        raise


async def process_uploaded_image(
    file_path: str,
    generate_thumbnails: bool = True
) -> dict:
    """
    Process an uploaded image - generate thumbnails and return metadata
    """
    result = {
        "original": file_path,
        "thumbnails": {}
    }
    
    if not generate_thumbnails:
        return result
    
    # Check if it's an image
    ext = Path(file_path).suffix.lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        return result
    
    # Generate thumbnails for each size
    for size_name in ["small", "medium"]:
        thumb_url = await generate_thumbnail(file_path, size_name)
        if thumb_url:
            result["thumbnails"][size_name] = thumb_url
    
    return result


async def get_thumbnail_url(original_url: str, size: str = "medium") -> str:
    """
    Get thumbnail URL for an existing image
    Returns original URL if thumbnail doesn't exist
    """
    if not original_url:
        return original_url
    
    # Extract filename from URL
    filename = original_url.split('/')[-1]
    name, ext = os.path.splitext(filename)
    
    thumb_name = f"{name}_{size}{ext}"
    thumb_path = THUMBNAIL_DIR / thumb_name
    
    if thumb_path.exists():
        return f"/api/uploads/thumbnails/{thumb_name}"
    
    # Try to generate it
    original_path = str(UPLOAD_DIR / original_url.replace('/api/uploads/', ''))
    thumb_url = await generate_thumbnail(original_path, size)
    
    return thumb_url or original_url


def get_image_dimensions(file_path: str) -> Optional[Tuple[int, int]]:
    """Get image dimensions without loading full image"""
    try:
        with Image.open(file_path) as img:
            return img.size
    except Exception:
        return None


async def cleanup_orphan_thumbnails():
    """Remove thumbnails for deleted images"""
    try:
        count = 0
        for thumb_file in THUMBNAIL_DIR.glob("*"):
            # Extract original filename
            name = thumb_file.stem
            for size in THUMBNAIL_SIZES.keys():
                if name.endswith(f"_{size}"):
                    original_name = name[:-len(f"_{size}")] + thumb_file.suffix
                    break
            else:
                continue
            
            # Check if original exists
            original_found = False
            for subdir in ['drawings', '3d_images', 'comments']:
                if (UPLOAD_DIR / subdir / original_name).exists():
                    original_found = True
                    break
            
            if not original_found:
                thumb_file.unlink()
                count += 1
        
        if count > 0:
            logger.info(f"Cleaned up {count} orphan thumbnails")
        
        return count
        
    except Exception as e:
        logger.error(f"Thumbnail cleanup error: {e}")
        return 0
