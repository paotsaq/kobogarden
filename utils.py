import sqlite3

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
    backwards: bool
        ) -> str:

    start_index = context.find(quote_to_expand)
    end_index = start_index + len(quote_to_expand)
    if backwards:
        new_index = context[start_index - 200:start_index].rfind('.')
        new_quote = context[start_index - 200 + new_index + 1:end_index].strip()
    else:
        new_index = context[start_index:end_index + 200].find('.')
        new_quote = context[start_index:new_index].strip()
    return new_quote
