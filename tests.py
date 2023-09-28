import unittest
from bs4 import BeautifulSoup
import sqlite3
from ebooklib import epub, ITEM_DOCUMENT

TEST_EPUB_FILE = 'jane-eyre.epub'
DESIRED_SENTENCE = """It is in vain to say human beings ought to be satisfied with tranquillity: they must have action, and they will make it if they cannot find it."""
ANOTHER_DESIRED_SENTENCE = """if she were a nice, pretty child, one might compassionate her forlornness"""


SQLITE_DB_PATH = "/users/alexj/kobo_highlights/"
SQLITE_DB_NAME = "test_kobo_db.sqlite"
EXISTING_IDS_FILE = "~/home/apinto/paogarden/existing_ids.txt"
class TestingKoboDatabase(unittest.TestCase):
    def test_can_open_kobo_database(self):
        conn = sqlite3.connect(SQLITE_DB_PATH + SQLITE_DB_NAME)
        c = conn.cursor()
        self.assertTrue(type(c) == sqlite3.Cursor)

    def test_can_retrieve_a_particular_bookmark_from_ID(self):
        conn = sqlite3.connect(SQLITE_DB_PATH + SQLITE_DB_NAME)
        c = conn.cursor()

        # Execute the SQL query
        c.execute("""
        SELECT
        Bookmark.BookmarkId,
        content.title as BookTitle,
        Bookmark.Text,
        Bookmark.DateCreated
        FROM "Bookmark"
        LEFT OUTER JOIN content
        ON (content.contentID=Bookmark.VolumeID and content.ContentType=6)
        WHERE
        BookmarkID="94ace0c6-b132-48b1-b0d9-1ef0e38db1ed"
        """)
        rows = c.fetchall()
        print(rows)

    # this will be useful to be able to select 
    # quotes just from a particular book and author.
    # NOTE how to make this on a single query?
    def test_can_retrieve_a_list_of_books_which_have_highlights(self):
        conn = sqlite3.connect(SQLITE_DB_PATH + SQLITE_DB_NAME)
        c = conn.cursor()

        # Execute the SQL query
        c.execute("""
        SELECT
        content.title as BookTitle,
        Bookmark.Text,
        Bookmark.DateCreated
        FROM "Bookmark"
        LEFT OUTER JOIN content
        ON (content.contentID=Bookmark.VolumeID and content.ContentType=6)
        WHERE
        BookmarkID="94ace0c6-b132-48b1-b0d9-1ef0e38db1ed"
        """)
        rows = c.fetchall()
        print(rows)


class TestingParsingEpubFiles(unittest.TestCase):
    def test_can_open_epub_file(self):
        book = epub.read_epub(TEST_EPUB_FILE)
        self.assertTrue(type(book) == epub.EpubBook)

    # epubs are fundamentally HTML files,
    # which should be pre-processed with BeautifulSoup
    # NOTE this is not the correct approach;
    # highlights already have the exact location of the quote;
    # I only need to provide the surrounding context, and, later,
    # an option to expand or contract the quote.
    def test_can_read_parsed_epub_file(self):
        book = epub.read_epub(TEST_EPUB_FILE)
        for item in book.get_items_of_type(ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text = soup.get_text()
            print(text)
            if DESIRED_SENTENCE in text:
                print("FOUND IT")
            input()

if __name__ == '__main__':
    unittest.main()
