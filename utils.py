import sqlite3
from bs4 import BeautifulSoup
from ebooklib import epub

SQLITE_DB_PATH = "./"
SQLITE_DB_NAME = "test_kobo_db.sqlite"
EXISTING_IDS_FILE = "./existing_ids.txt"


def create_connection_to_database(
        path: str
        ) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    return conn


def get_all_highlights_of_book_from_database(
        book_name: str
        ) -> list[str]:
    """returns a list with
    full highlight content and date of highlight"""
    conn = create_connection_to_database(SQLITE_DB_PATH + SQLITE_DB_NAME)
    c = conn.cursor()
    c.execute(f"""
    SELECT
    Bookmark.Text,
    Bookmark.DateCreated
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


def get_highlight_from_database(
        highlight_id: str
        ) -> list[str]:
    """returns a list with
    title of book, full highlight content, date of highlight,
    start of highlight, end of highlight"""
    conn = create_connection_to_database(SQLITE_DB_PATH + SQLITE_DB_NAME)
    c = conn.cursor()
    c.execute(f"""
    SELECT
    content.title as BookTitle,
    Bookmark.Text,
    Bookmark.DateCreated,
    StartContainerPath,
    EndContainerPath
    FROM "Bookmark"
    LEFT OUTER JOIN content
    ON (content.contentID=Bookmark.VolumeID and content.ContentType=6)
    WHERE
    BookmarkID="{highlight_id}"
    """)
    content = c.fetchall()[0]
    conn.close()
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
    """)
    results = c.fetchall()  # Fetch all results
    conn.close()
    parsed = [
            [title, author, take_epub_file_name_from_path(file)]
            for title, author, file in results
            ]
    return parsed


def expand_quote(
    quote_to_expand: str,
    context: str,
    backwards: bool,
    cons: int = 200
        ) -> str:
    start_index = context.find(quote_to_expand[:-1])
    if start_index == -1:
        print("Could not find context!")
        return ""
    end_index = start_index + len(quote_to_expand)
    if backwards:
        new_index = context[start_index - cons:start_index].rfind('.')
        if new_index == -1:
            return expand_quote(quote_to_expand, context, backwards, cons + 200)
        new_quote = context[start_index - cons + new_index + 1:end_index].strip()
    else:
        new_index = context[start_index:end_index + cons].rfind('.')
        if new_index == -1:
            return expand_quote(quote_to_expand, context, backwards, cons + 200)
        new_quote = context[start_index:start_index + new_index + 1].strip()
    return new_quote


def get_full_context_from_highlight(
        book_path: str,
        section_path: str
        ) -> str:
    book = epub.read_epub(book_path)
    if not book:
        raise FileNotFoundError("The book doesn't seem to exist?")
    section = None
    while section is None:
        section = book.get_item_with_href(section_path)
        section_path = "/".join(section_path.split("/")[1:])
    soup = BeautifulSoup(section.get_content(), 'html.parser').get_text()
    return soup
