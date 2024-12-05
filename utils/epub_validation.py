from ebooklib import epub
from pathlib import Path
from functools import lru_cache
from utils.logging import logging
from bs4 import BeautifulSoup
from utils.const import BOOKS_DIR
from urllib.parse import unquote


@lru_cache(maxsize=100)
def validate_epub_structure(book_path: str) -> tuple[bool, str]:
    """
    Validates basic epub structure and returns (is_valid, error_message)
    """
    full_path = Path(BOOKS_DIR) / book_path
    if not full_path.exists():
        return False, f"Book file not found: {full_path}"
    
    try:
        book = epub.read_epub(str(full_path))
        
        # Check if book has basic required elements
        if not book.spine:
            return False, "No spine items found in epub"
            
        if not book.get_metadata('DC', 'title'):
            return False, "No title metadata found"
            
        # Check if all referenced sections exist
        for item in book.get_items():
            if hasattr(item, 'get_content'):
                if not item.get_content():
                    return False, f"Empty or invalid content in section: {item.get_name()}"
                    
        return True, "Valid epub structure"
        
    except Exception as e:
        return False, f"Error validating epub: {str(e)}" 

# provides the full content of the .html file
# in which a given highlight can be found. Highlights in Kobo
# will carry information about the section in which they are.
# Then, the highlight must be found inside the section
# (and the section can be quite big).
def get_full_context_from_highlight(
        book_path: str,
        section_path: str
        ) -> str:
    # First validate the epub
    is_valid, error_msg = validate_epub_structure(book_path)
    if not is_valid:
        logging.error(f"Invalid epub structure: {error_msg}")
        return None

    book = epub.read_epub(book_path, {"ignore_ncx": True})
    
    # Try different path variations systematically
    original_path = unquote(section_path)
    section = None
    path_variations = []
    
    # Build list of possible paths
    path_parts = original_path.split('/')
    for i in range(len(path_parts)):
        variant = '/'.join(path_parts[i:])
        path_variations.append(variant)
    
    # Try each variation
    for path in path_variations:
        logging.debug(f"Trying to find section with path: {path}")
        section = book.get_item_with_href(path)
        if section:
            logging.debug(f"Found section using path: {path}")
            break
    
    if section is None:
        logging.error(f"Could not find section. Tried variations of: {original_path}")
        return None

    try:
        soup = BeautifulSoup(section.get_content(), 'html.parser').get_text()
        return soup
    except Exception as e:
        logging.error(f"Error parsing section content: {str(e)}")
        return None