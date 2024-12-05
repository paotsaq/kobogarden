from zipfile import ZipFile
import xml.etree.ElementTree as ET
from pathlib import Path
from utils.const import IMAGE_FILES_PATH
from utils.logging import logging
from typing import Optional

def extract_cover_from_epub(epub_path: str, book_name: str) -> Optional[str]:
    """
    Extract cover image from epub file and save it to images directory.
    Returns the filename of the saved cover if successful, None otherwise.
    """
    logging.debug(f"Extracting cover from epub: {epub_path}")
    try:
        with ZipFile(epub_path, 'r') as epub:
            # First try to find cover in the OPF file
            opf_files = [f for f in epub.namelist() if f.endswith('.opf')]
            if not opf_files:
                return None
                
            # Get OPF directory to resolve relative paths
            opf_dir = str(Path(opf_files[0]).parent)
                
            # Parse OPF to find cover image path
            opf_content = epub.read(opf_files[0])
            root = ET.fromstring(opf_content)
            
            # Look for cover image in metadata
            ns = {'opf': 'http://www.idpf.org/2007/opf'}
            cover_id = None
            for meta in root.findall('.//opf:meta[@name="cover"]', ns):
                cover_id = meta.get('content')
                break
                
            if cover_id:
                # Find the actual image file
                for item in root.findall('.//opf:item', ns):
                    if item.get('id') == cover_id:
                        cover_path = item.get('href')
                        # Resolve relative path
                        if opf_dir:
                            cover_path = str(Path(opf_dir) / cover_path)
                        break
            else:
                # Fallback: look for likely cover image files
                cover_path = next(
                    (f for f in epub.namelist() 
                     if 'cover' in f.lower() and f.endswith(('.jpg', '.jpeg', '.png'))),
                    None
                )
            
            if not cover_path:
                return None
                
            logging.debug(f"Attempting to extract cover from path: {cover_path}")
            
            try:
                # Extract cover image
                cover_data = epub.read(cover_path)
            except KeyError:
                # If that fails, try without the opf directory
                base_cover_path = Path(cover_path).name
                logging.debug(f"Retrying with base path: {base_cover_path}")
                cover_data = epub.read(base_cover_path)
            
            cover_ext = Path(cover_path).suffix.lower()[1:]  # Remove the dot
            
            # Create new filename for the cover
            parsed_book_name = book_name.replace(" ", "-").lower()
            new_cover_filename = f"book-cover-{parsed_book_name}.{cover_ext}"
            
            # Save cover to images directory
            cover_path = Path(IMAGE_FILES_PATH) / new_cover_filename
            cover_path.write_bytes(cover_data)
            
            logging.info(f"Extracted cover image to: {cover_path}")
            return new_cover_filename
            
    except Exception as e:
        logging.error(f"Failed to extract cover from epub: {e}")
        logging.debug("Available files in epub:", epub.namelist())
        return None