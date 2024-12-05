import sqlite3
from typing import Optional
import logging
from pathlib import Path
from utils.logging import logging
from utils.const import (
    SQLITE_DB_PATH,
    SQLITE_DB_NAME,
    BOOKS_DIR,
    )
from utils.epub_validation import validate_epub_structure


class DatabaseError(Exception):
    """Base class for database-related errors"""
    pass


class BookNotFoundError(DatabaseError):
    """Raised when a book cannot be found in the database"""
    pass


def create_connection_to_database(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    return conn


def get_book_details_from_book_name(book_name: str) -> tuple[str, str, str]:
    """
    Get the filename, title, and author for a book from its name.
    
    Args:
        book_name: The title of the book as displayed in the interface
        
    Returns:
        tuple: (filename, title, author)
        
    Raises:
        BookNotFoundError: If the book is not found in the database
        DatabaseError: If there's an error accessing the database
    """
    try:
        conn = create_connection_to_database(SQLITE_DB_PATH + SQLITE_DB_NAME)
        if not conn:
            raise DatabaseError("Could not connect to database")
            
        c = conn.cursor()
        
        # Get all relevant fields from the database
        c.execute("""
            SELECT 
                content.BookId,
                content.Title as BookTitle,
                content.Attribution as BookAuthor,
                content.ContentID  -- Adding ContentID as a fallback
            FROM content 
            WHERE content.Title LIKE ? 
            OR content.Title LIKE ?
        """, (
            f"%{book_name}%",
            f"%{book_name.split(' by ')[0]}%"
        ))
        
        result = c.fetchall()
        if not result:
            raise BookNotFoundError(f"No book found with title: {book_name}")
            
        book_id, title, author, content_id = result[0]
        
        # Try to get a valid identifier (either BookId or ContentID)
        identifier = book_id if book_id else content_id
        if not identifier:
            logging.error(f"Book found but no valid identifier. Title: {title}, Author: {author}")
            raise BookNotFoundError(f"Book metadata exists but no valid identifier found: {title}")
            
        filename = identifier.split('/')[-1]
        if not filename.endswith('.epub'):
            filename += '.epub'
            
        # Verify the file exists
        full_path = Path(BOOKS_DIR) / filename
        if not full_path.exists():
            raise BookNotFoundError(f"Book file not found at: {full_path}")
            
        return filename, title, author
        
    except sqlite3.Error as e:
        logging.error(f"Database error for book '{book_name}': {str(e)}")
        raise DatabaseError(f"Database error: {str(e)}")
        
    finally:
        if 'conn' in locals() and conn:
            conn.close()


# returns a list with
# full highlight content and date of highlight
def get_all_highlights_of_book_from_database(
        book_name: str
        ) -> list[tuple]:
    """
    Get all highlights for a specific book.
    
    Args:
        book_name: The title of the book
        
    Returns:
        list[tuple]: List of highlight tuples (text, date_created, bookmark_id, start_container_path)
        
    Raises:
        BookNotFoundError: If the book is not found in the database
        DatabaseError: If there's an error accessing the database
    """
    try:
        conn = create_connection_to_database(SQLITE_DB_PATH + SQLITE_DB_NAME)
        if not conn:
            raise DatabaseError("Could not connect to database")
            
        c = conn.cursor()
        
        # First get the ContentID for this book
        c.execute("""
            SELECT ContentID
            FROM content 
            WHERE Title=? AND ContentType=6
            LIMIT 1
        """, (book_name,))
        
        result = c.fetchone()
        if not result:
            raise BookNotFoundError(f"No book found with title: {book_name}")
            
        content_id = result[0]
        
        # Then get all highlights for this specific ContentID
        c.execute("""
            SELECT
                Bookmark.Text,
                Bookmark.DateCreated,
                BookmarkID,
                StartContainerPath
            FROM "Bookmark"
            LEFT OUTER JOIN content
            ON (content.contentID=Bookmark.VolumeID and content.ContentType=6)
            WHERE content.ContentID=?
            ORDER BY Bookmark.DateCreated
        """, (content_id,))
        
        all_highlights = c.fetchall()
        logging.debug(f"Found {len(all_highlights)} highlights for book '{book_name}'")
        return all_highlights
        
    except sqlite3.Error as e:
        logging.error(f"Database error getting highlights for '{book_name}': {str(e)}")
        raise DatabaseError(f"Database error: {str(e)}")
        
    finally:
        if 'conn' in locals() and conn:
            conn.close()


# returns a list with
# title of book, full highlight content, date of highlight,
# highlight, container_path, epub file name"""
def get_highlight_from_database(
        highlight_id: str
        ) -> tuple:
    conn = create_connection_to_database(SQLITE_DB_PATH + SQLITE_DB_NAME)
    c = conn.cursor()
    c.execute(f"""
    SELECT
    content.title as BookTitle,
    content.attribution as BookAuthor,
    Bookmark.Text,
    Bookmark.DateCreated,
    StartContainerPath,
    Bookmark.VolumeID
    FROM "Bookmark"
    LEFT OUTER JOIN content
    ON (content.contentID=Bookmark.VolumeID and content.ContentType=6)
    WHERE
    BookmarkID="{highlight_id}"
    """)
    # 240106: there was a bug in matching certain quotes;
    # it was due to `quote_to_expand` being preceded by whitespace.
    # the `.strip()` seems to be a fix.
    content = c.fetchall()[0]
    fixed_path = content[5].split('/')[-1]
    content = list(content[:5]) + [fixed_path]
    if fixed_path[-5:] != '.epub':
        raise FileNotFoundError
    conn.close()
    content[2] = content[2].strip()
    # Validate before returning
    is_valid, error_msg = validate_epub_structure(fixed_path)
    if not is_valid:
        logging.warning(f"Book {fixed_path} has invalid structure: {error_msg}")
    return (content[0], content[1], content[2], content[3], content[4], fixed_path)


# returns a list of lists of three strings
def get_list_of_highlighted_books(
        sqlite_db_path: str
        ) -> list[list[str, str, str]]:
    def take_epub_file_name_from_path(path: str):
        return path.split('/')[-1]
    conn = create_connection_to_database(sqlite_db_path)
    c = conn.cursor()
    c.execute("""
    WITH LatestHighlights AS (
        SELECT 
            content.ContentID,
            MAX(Bookmark.DateCreated) as LastHighlightDate
        FROM "Bookmark"
        LEFT OUTER JOIN content
        ON (content.contentID=Bookmark.VolumeID and content.ContentType=6)
        GROUP BY content.ContentID
    )
    SELECT DISTINCT
        content.Title as BookTitle,
        content.Attribution,
        content.ContentID,
        lh.LastHighlightDate
    FROM "Bookmark"
    LEFT OUTER JOIN content
    ON (content.contentID=Bookmark.VolumeID and content.ContentType=6)
    LEFT OUTER JOIN LatestHighlights lh
    ON content.ContentID = lh.ContentID
    WHERE content.Attribution IS NOT NULL
    ORDER BY lh.LastHighlightDate DESC
    """)
    results = c.fetchall()  # Fetch all results
    conn.close()
    parsed = [
            [title, author, take_epub_file_name_from_path(file)]
            for title, author, file, _ in results
            ]
    return parsed
