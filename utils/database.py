import sqlite3
from utils.logging import logging
from utils.const import (
    SQLITE_DB_PATH,
    SQLITE_DB_NAME,
    )
from utils.epub_validation import validate_epub_structure


def create_connection_to_database(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    return conn


def get_book_filename_from_book_name(book_name: str) -> str:
    print("BOOK NAME IS ", book_name)
    conn = create_connection_to_database(SQLITE_DB_PATH + SQLITE_DB_NAME)
    c = conn.cursor()
    c.execute(f"""SELECT BookId from content where BookTitle="{book_name}";""")
    content = c.fetchall()[0][0]
    fixed_path = content.split('/')[-1]
    if fixed_path[-5:] != '.epub':
        raise FileNotFoundError
    return fixed_path


# returns a list with
# full highlight content and date of highlight
def get_all_highlights_of_book_from_database(
        book_name: str
        ) -> list[str]:
    conn = create_connection_to_database(SQLITE_DB_PATH + SQLITE_DB_NAME)
    c = conn.cursor()
    # First get the ContentID for this book
    c.execute(f"""
    SELECT ContentID
    FROM content 
    WHERE Title="{book_name}" AND ContentType=6
    LIMIT 1
    """)
    content_id = c.fetchone()[0]
    
    # Then get all highlights for this specific ContentID
    c.execute(f"""
    SELECT
    Bookmark.Text,
    Bookmark.DateCreated,
    BookmarkID,
    StartContainerPath
    FROM "Bookmark"
    LEFT OUTER JOIN content
    ON (content.contentID=Bookmark.VolumeID and content.ContentType=6)
    WHERE
    content.ContentID="{content_id}"
    ORDER BY Bookmark.DateCreated
    """)
    content = c.fetchall()
    conn.close()
    return content


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
