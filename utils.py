import sqlite3
from bs4 import BeautifulSoup
from ebooklib import epub

SQLITE_DB_PATH = "./"
SQLITE_DB_NAME = "test_kobo_db.sqlite"
EXISTING_IDS_FILE = "/home/apinto/paogarden/existing_ids.txt"


def create_connection_to_database(
        path: str
        ) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    return conn


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
        highlight: str,
        book_path: str,
        section_path: str
        ) -> str:
        book = epub.read_epub(book_path)
        if not book:
            raise FileNotFoundError("The book doesn't seem to exist?")
        section = None
        while section is None:
            section = book.get_item_with_href(section_path)

        soup = BeautifulSoup(section.get_content(), 'html.parser').get_text()
        return soup
