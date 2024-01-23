import sqlite3
from utils.const import (
    SQLITE_DB_PATH,
    SQLITE_DB_NAME,
    )


def create_connection_to_database(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    return conn


# returns a list with
# full highlight content and date of highlight
def get_all_highlights_of_book_from_database(
        book_name: str
        ) -> list[str]:
    conn = create_connection_to_database(SQLITE_DB_PATH + SQLITE_DB_NAME)
    c = conn.cursor()
    c.execute(f"""
    SELECT
    Bookmark.Text,
    Bookmark.DateCreated,
    BookmarkID
    FROM "Bookmark"
    LEFT OUTER JOIN content
    ON (content.contentID=Bookmark.VolumeID and content.ContentType=6)
    WHERE
    content.Title="{book_name}"
    ORDER BY Bookmark.DateCreated
    """)
    content = c.fetchall()
    conn.close()
    return content


# returns a list with
# title of book, full highlight content, date of highlight,
# start of highlight, epub file name"""
def get_highlight_from_database(
        highlight_id: str
        ) -> list[str]:
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
    return content


def get_list_of_highlighted_books(
        sqlite_db_path: str
        ):
    def take_epub_file_name_from_path(path: str):
        return path.split('/')[-1]
    conn = create_connection_to_database(sqlite_db_path)
    c = conn.cursor()
    # Execute the SQL query
    c.execute("""
    SELECT 
        unique_book_titles.BookTitle,
        content.Attribution,
        content.ContentID
    FROM 
        (SELECT DISTINCT content.title as BookTitle
        FROM "Bookmark"
        LEFT OUTER JOIN content
        ON (content.contentID=Bookmark.VolumeID and content.ContentType=6)) as unique_book_titles
    LEFT OUTER JOIN content
    ON unique_book_titles.BookTitle = content.Title
    WHERE content.Attribution IS NOT NULL
    """)
    results = c.fetchall()  # Fetch all results
    conn.close()
    parsed = [
            [title, author, take_epub_file_name_from_path(file)]
            for title, author, file in results
            ]
    return parsed
