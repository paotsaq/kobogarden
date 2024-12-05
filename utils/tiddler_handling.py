from os import listdir
from datetime import datetime
from utils.const import (
    PAOGARDEN_DIR,
    TIDDLERS_PATH,
    EXISTING_IDS_FILE
        )
from pathlib import Path
import re
from typing import Optional, Tuple
from utils.logging import logging

try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False
    print("Warning: pyperclip not installed. Clipboard functionality will be disabled.")


def produce_fhl_tiddler_string(
        created_timestamp: str,
        book: str,
        ) -> str:
    """The function is only responsible for creating
    the full highlights list tiddler;
    """
    return f"""created: {created_timestamp}
creator: kobogarden
created: {created_timestamp}
modifier: kobogarden
modified: {created_timestamp}
tags: fhl
title: fhl-{book}
type: text/vnd.tiddlywiki

\\import [tag[macro]]

<$list filter="[tag[book-quote]tag[{book}]sort[quote-order]]">
   <$macrocall $name="renderClickableTitle" tiddler=<<currentTiddler>> />
</$list>
"""


def produce_book_tiddler_string(
        created_timestamp: str,
        book: str,
        author: str,
        ) -> str:
    """The function is only responsible for creating
    the book tiddler; it will be necessary to update the
    `nbr_of_highlights` field on a separate function; by
    default, it will start at 1 (book tiddlers are created
    in the single highlight panel)"""
    return f"""created: {created_timestamp}
creator: kobogarden
created: {created_timestamp}
modifier: kobogarden
modified: {created_timestamp}
tags: book
title: {book}
author: {author}
nbr_of_highlights: 1
type: text/vnd.tiddlywiki

\\import [tag[macro]]

//[the notes from the book were retrieved with [[kobogarden]], with the purpose of aiding to create a map of the ideas the book left me. The full list of book highlights can be found [[here|fhl-{book}]].]//

<div style="float: left; margin: 0 40px 8px 0;
                  width: 30%;
                  justify-content: space-between;
                  align-content: space-between;
                  max-width: 200px">
<$image source={{!!book-cover-tiddler}}/>
</div>
"""

def check_tiddler_exists(tiddler_title: str) -> bool:
    """Check if a tiddler with the given title exists"""
    return (tiddler_title + '.tid') in listdir(TIDDLERS_PATH)


def copy_to_clipboard(text: str) -> None:
    """Copy text to clipboard if pyperclip is available"""
    if HAS_CLIPBOARD:
        try:
            pyperclip.copy(text)
            logging.info(f"Copied to clipboard: {text}")
        except Exception as e:
            logging.error(f"Failed to copy to clipboard: {e}")


def create_book_tiddler(
        book_title: str,
        book_author: str
        ) -> None:
    if check_tiddler_exists(book_title):
        logging.warning(f"Warning: Tiddler '{book_title}' already exists!")
        return
        
    formatted_now = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
    book_content = produce_book_tiddler_string(formatted_now, book_title, book_author)
    fhl_content = produce_fhl_tiddler_string(formatted_now, book_title)
    with open(TIDDLERS_PATH + book_title + '.tid', 'w') as file:
        file.write(book_content)
    logging.info("Created book tiddler: " + book_title)
    copy_to_clipboard(book_title)
    
    with open(TIDDLERS_PATH + 'fhl-' + book_title + '.tid', 'w') as file:
        file.write(fhl_content)
    logging.info("Created fhl tiddler: " + book_title)


def increment_book_tiddler_highlight_number(book_title: str) -> int:
    """The function increments the book tiddler highlight number,
    but also returns the number of highlights"""
    with open(TIDDLERS_PATH + book_title + '.tid', 'r') as file:
        content = file.read()

    lines = content.splitlines()
    # takes the line corresponding to the nbr_of_highlights information
    index, line = next(filter(lambda pair: 'nbr_of_highlights' in pair[1],
                       enumerate(lines)))
    new_highlight_count = int(line.split()[1]) + 1
    new_lines = (lines[:index] +
                 [f'nbr_of_highlights: {new_highlight_count}'] +
                 lines[index + 1:])
    with open(TIDDLERS_PATH + book_title + '.tid', 'w') as file:
        content = file.write("\n".join(new_lines))
    return new_highlight_count


# 240322 - adds a book-quote tiddler by default
def produce_highlight_tiddler_string(
        created_timestamp: str,
        tags: list,
        highlight_title: str,
        comment: str,
        highlight: str,
        quote_order: int,
        chapter: str = ""
        ) -> str:
    return f"""created: {created_timestamp}
creator: kobogarden
created: {created_timestamp}
modifier: kobogarden
modified: {created_timestamp}
tags: {" ".join(["book-quote"] + tags)}
title: {highlight_title}
chapter: {chapter}
type: text/vnd.tiddlywiki
quote-order: {'0' if quote_order < 10 else ''}{str(quote_order)}
{"\n" + comment + "\n" if comment else ""}
<<<
{highlight}
<<<
"""


def record_in_highlight_id(highlight_id: str) -> bool:
    with open(TIDDLERS_PATH + EXISTING_IDS_FILE, "r") as file:
        return highlight_id in file.read().splitlines()


def add_highlight_id_to_record(highlight_id: str) -> None:
    """This function doesn't check whether the highlight already exists!"""
    with open(TIDDLERS_PATH + EXISTING_IDS_FILE, "a") as file:
        file.write('\n\n' + highlight_id + '\n\n')


class TiddlerFilenameManager:
    def __init__(self):
        self.mappings_file = Path(PAOGARDEN_DIR) / "book_metadata_mappings.txt"
        # Create mappings file if it doesn't exist
        self.mappings_file.touch(exist_ok=True)
        self.metadata_cache = {}  # Initialize empty, will be loaded when needed

    
    def refresh_metadata(self) -> None:
        """Reload metadata from file - call this when opening the modal"""
        self.metadata_cache.clear()
        with open(self.mappings_file, 'r') as f:
            for line in f:
                if line.strip():
                    filename, title, author = line.strip().split('|')
                    self.metadata_cache[self._clean_filename(filename)] = (title.strip(), author.strip())
        logging.info("Refreshed book metadata from file")

    def get_mapped_metadata(self, original_filename: str) -> Tuple[str, str]:
        """Get title and author from mappings file"""
        clean_original = self._clean_filename(original_filename)
        
        with open(self.mappings_file, 'r') as f:
            for line in f:
                if line.strip():  # Skip empty lines
                    filename, title, author = line.strip().split('|')
                    if self._clean_filename(filename) == clean_original:
                        return title.strip(), author.strip()
        
        # If no mapping found, return original parsed
        return self._parse_original_name(original_filename)
    
    def _clean_filename(self, filename: str) -> str:
        """Remove extension and clean up the filename for comparison"""
        return re.sub(r'[^\w\s-]', '', filename.replace('.epub', '').strip().lower())
    
    def _parse_original_name(self, original_name: str) -> Tuple[str, str]:
        """Parse original filename into title and author"""
        # Handle common filename patterns
        # Example: "Author, Name - Book Title.epub"
        # or "Book Title - Author Name.epub"
        name = original_name.replace('.epub', '')
        
        if " - " in name:
            parts = name.split(" - ", 1)
            # Check if first part looks like an author (contains comma or is shorter)
            if "," in parts[0] or len(parts[0].split()) <= 3:
                return parts[1], parts[0]
            return parts[0], parts[1]
        
        return name, ""  # fallback if no clear pattern
    
    def update_metadata_mapping(self, original_filename: str, title: str, author: str) -> None:
        """Update or add a mapping in the mappings file"""
        clean_original = self._clean_filename(original_filename)
        current_mappings = []
        
        # Read existing mappings, excluding the one we're updating
        if self.mappings_file.exists():
            with open(self.mappings_file, 'r') as f:
                for line in f:
                    if line.strip():
                        filename, _, _ = line.strip().split('|')
                        if self._clean_filename(filename) != clean_original:
                            current_mappings.append(line.strip())
        
        # Add the new mapping
        current_mappings.append(f"{original_filename}|{title}|{author}")
        
        # Write all mappings back to file
        with open(self.mappings_file, 'w') as f:
            f.write('\n'.join(current_mappings) + '\n')
        
        logging.info(f"Updated metadata mapping for {original_filename}")

class TiddlerError(Exception):
    """Base exception for tiddler-related errors"""
    pass

class TiddlerExistsError(TiddlerError):
    """Raised when attempting to create a tiddler that already exists"""
    pass

def create_highlight_tiddler(
        tiddler_title: str,
        highlight: str,
        original_filename: str,
        tags: list,
        comment: str = "",
        chapter: str = ""
        ) -> Optional[str]:

    if check_tiddler_exists(tiddler_title):
        raise TiddlerExistsError(f"Tiddler with title '{tiddler_title}' already exists")

    """Create a tiddler with filename-based metadata mapping.
    This was implemented because we might have changed the author,
    or title of a book. The filename is the only constant metadata"""
    manager = TiddlerFilenameManager()
    title, author = manager.get_mapped_metadata(original_filename)
    
    # Access or create book tiddler, and retrieve the `highlight_order`
    if check_tiddler_exists(title):
        highlight_order = increment_book_tiddler_highlight_number(title)
    else:
        create_book_tiddler(title, author)
        highlight_order = 1

    
    # Create tiddler content
    content = produce_highlight_tiddler_string(
        created_timestamp=datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3],
        tags=tags,
        highlight_title=tiddler_title,
        comment=comment,
        highlight=highlight,
        quote_order=highlight_order,
        chapter=chapter,
    )
    
    # Save tiddler
    try:
        with open(Path(TIDDLERS_PATH) / tiddler_title / '.tid', 'w') as f:
            f.write(content)
        return tiddler_title
    except Exception as e:
        logging.error(f"Failed to create tiddler: {e}")
        return None
