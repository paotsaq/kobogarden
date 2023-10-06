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
    def test_can_retrieve_jane_eyre_highlight_content_from_ID(self):
        rows = get_highlight_from_database("94ace0c6-b132-48b1-b0d9-1ef0e38db1ed")
        self.assertEqual(rows[0], 'Jane Eyre: An Autobiography')
        self.assertEqual(rows[1], '\nI had made no noise: he had not eyes behind—could his shadow feel?')
        self.assertEqual(rows[2], '2023-08-30T18:09:48.000')
        self.assertEqual(rows[3], 'OEBPS/6048514455528670785_1260-h-25.htm.html#point(/1/4/1/21:1)')
        self.assertEqual(rows[4], 'OEBPS/6048514455528670785_1260-h-25.htm.html#point(/1/4/1/22/1:69)')

    def test_can_retrieve_berlin_highlight_content_from_ID(self):
        rows = get_highlight_from_database("f27d6696-d59a-4cb1-a329-310fd17d6eea")
        self.assertEqual(rows[0], 'The Ghosts of Berlin: Confronting German History in the Urban Landscape')
        self.assertEqual(rows[1], 'The relationship between the gate and the all-important circulation of traffic sparked another debate. The attachment many Germans have to their cars has always stopped short of the American practice of tearing down cities to make way for cars, but the passion of German car lovers seems to arouse in Green-thinking Germans the same kind of suspicion that passionate patriotism does.')
        self.assertEqual(rows[2], '2023-08-30T06:13:56.000')
        self.assertEqual(rows[3], 'text/part0011.html#point(/1/4/192/3:147)')
        self.assertEqual(rows[4], 'text/part0011.html#point(/1/4/192/3:530)')
        self.quote = rows[1]
        self.quote_location = rows[3]

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
        book = epub.read_epub(TEST_EPUB_BERLIN)
        self.assertTrue(type(book) == epub.EpubBook)

    # epubs are fundamentally HTML files,
    # which should be pre-processed with BeautifulSoup
    # NOTE this is not the correct approach;
    # highlights already have the exact location of the quote;
    # I only need to provide the surrounding context, and, later,
    # an option to expand or contract the quote.
    def test_can_find_quote_in_epub_file(self):
        book = epub.read_epub(TEST_EPUB_BERLIN)
        quote = 'The relationship between the gate and the all-important circulation of traffic sparked another debate. The attachment many Germans have to their cars has always stopped short of the American practice of tearing down cities to make way for cars, but the passion of German car lovers seems to arouse in Green-thinking Germans the same kind of suspicion that passionate patriotism does.'
        section = book.get_item_with_href('text/part0011.html')
        soup = BeautifulSoup(section.get_content(), 'html.parser').get_text()
        start_index = soup.find(quote)
        end_index = start_index + len(quote)
        print(start_index)
        print(end_index)
        print(soup[start_index:end_index + 1])

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
