import sqlite3

SQLITE_DB_PATH = "./"
SQLITE_DB_NAME = "test_kobo_db.sqlite"
EXISTING_IDS_FILE = "/home/apinto/paogarden/existing_ids.txt"


def create_connection_to_database(
        path: str
        ) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    return conn


def get_highlight_from_database(highlight_id: str):
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
