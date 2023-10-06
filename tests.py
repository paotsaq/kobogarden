import unittest
from utils import (
        create_connection_to_database,
        get_highlight_from_database
        )
from bs4 import BeautifulSoup
import sqlite3
from ebooklib import epub, ITEM_DOCUMENT

TEST_EPUB_JANEEYRE = 'jane-eyre.epub'
TEST_EPUB_BERLIN = 'berlin.epub'
DESIRED_SENTENCE = """It is in vain to say human beings ought to be satisfied with tranquillity: they must have action, and they will make it if they cannot find it."""
ANOTHER_DESIRED_SENTENCE = """if she were a nice, pretty child, one might compassionate her forlornness"""


SQLITE_DB_PATH = "./"
SQLITE_DB_NAME = "test_kobo_db.sqlite"
EXISTING_IDS_FILE = "~/home/apinto/paogarden/existing_ids.txt"


class TestingKoboDatabase(unittest.TestCase):
    def test_can_open_kobo_database(self):
        conn = sqlite3.connect(SQLITE_DB_PATH + SQLITE_DB_NAME)
        c = conn.cursor()
        self.assertTrue(type(c) == sqlite3.Cursor)

    # returns many fields from the query
    def test_can_retrieve_highlight_content_from_ID(self):
        rows = get_highlight_from_database("94ace0c6-b132-48b1-b0d9-1ef0e38db1ed")
        self.assertEqual(rows[0], 'Jane Eyre: An Autobiography')
        self.assertEqual(rows[1], '\nI had made no noise: he had not eyes behind—could his shadow feel?')
        self.assertEqual(rows[2], '2023-08-30T18:09:48.000')
        self.assertEqual(rows[3], 'OEBPS/6048514455528670785_1260-h-25.htm.html#point(/1/4/1/21:1)')
        self.assertEqual(rows[4], 'OEBPS/6048514455528670785_1260-h-25.htm.html#point(/1/4/1/22/1:69)')

    # # this will be useful to be able to select 
    # # quotes just from a particular book and author.
    # # NOTE how to make this on a single query?
    # def test_can_retrieve_a_list_of_books_which_have_highlights(self):
        # conn = sqlite3.connect(SQLITE_DB_PATH + SQLITE_DB_NAME)
        # c = conn.cursor()

        # # Execute the SQL query
        # c.execute("""
        # SELECT
        # content.title as BookTitle,
        # Bookmark.Text,
        # Bookmark.DateCreated
        # FROM "Bookmark"
        # LEFT OUTER JOIN content
        # ON (content.contentID=Bookmark.VolumeID and content.ContentType=6)
        # WHERE
        # BookmarkID="94ace0c6-b132-48b1-b0d9-1ef0e38db1ed"
        # """)
        # rows = c.fetchall()
        # print(rows)


class TestingParsingEpubFiles(unittest.TestCase):
    def test_can_open_epub_file(self):
        book = epub.read_epub(TEST_EPUB_JANEEYRE)
        self.assertTrue(type(book) == epub.EpubBook)

    # epubs are fundamentally HTML files,
    # which should be pre-processed with BeautifulSoup
    # NOTE this is not the correct approach;
    # highlights already have the exact location of the quote;
    # I only need to provide the surrounding context, and, later,
    # an option to expand or contract the quote.
    # def test_can_read_parsed_epub_file(self):
        # book = epub.read_epub(TEST_EPUB_JANEEYRE)
        # for item in book.get_items_of_type(ITEM_DOCUMENT):
            # soup = BeautifulSoup(item.get_content(), 'html.parser')
            # text = soup.get_text()
            # print(text)
            # if DESIRED_SENTENCE in text:
                # print("FOUND IT")
            # input()

    # # trying to access Jane Eyre
    # def test_can_get_quote_using_container_path(self):
        # book = epub.read_epub(TEST_EPUB_JANEEYRE)
        # href = "OEBPS/6048514455528670785_1260-h-21.htm.html"
        # # item = book.get_item_with_href(href)
        # html_items = [item.file_name for item in list(book.get_items())]
        # print("6048514455528670785_1260-h-21.htm.html" in html_items)
        # print(html_items)

    # trying to access Berlin
    def test_can_get_another_quote_using_container_path(self):
        book = epub.read_epub(TEST_EPUB_BERLIN)
        # raw_db_href comes from the `StartContainerPath`;
        # I suppose all quotes will have the same path in both
        # `StartContainerPath` and `EndContainerPath`;
        # thus, it should be okay to assume the path is the same for both.
        raw_db_href = "OEBPS/xhtml/chapter20.xhtml#point(/1/4/68/1:165)"
        if "OEBPS/" == raw_db_href[:5]:
            path, point = raw_db_href[6:].split('#')
        # item = book.get_item_with_href(href)
        html_items = [item.file_name for item in list(book.get_items())]
        print("6048514455528670785_1260-h-21.htm.html" in html_items)
        # print(html_items)


if __name__ == '__main__':
    unittest.main()
