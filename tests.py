import unittest
from utils import (
        create_connection_to_database,
        get_highlight_from_database,
        expand_quote
        )
from bs4 import BeautifulSoup
import sqlite3
from ebooklib import epub, ITEM_DOCUMENT

TEST_EPUB_JANEEYRE = 'jane-eyre.epub'
TEST_EPUB_BERLIN = 'berlin.epub'
TEST_EPUB_BURN = 'burn.epub'
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

    # TODO refactor this into its own function.
    def test_can_retrieve_a_list_of_books_which_have_highlights(self):
        def take_epub_file_name_from_path(path: str):
            return path.split('/')[-1]
        conn = sqlite3.connect(SQLITE_DB_PATH + SQLITE_DB_NAME)
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

        parsed = [
                [title, author, take_epub_file_name_from_path(file)]
                for title, author, file in results
                ]
        self.assertIn(['The Ghosts of Berlin: Confronting German History in the Urban Landscape', 'Brian Ladd', '- The Ghosts of Berlin_ Confronting German History in the Urban Landscape.epub'], parsed)


class TestingFindingQuoteInEpubFiles(unittest.TestCase):
    def test_can_open_epub_file(self):
        book = epub.read_epub(TEST_EPUB_BERLIN)
        self.assertTrue(type(book) == epub.EpubBook)

    # epubs are fundamentally HTML files,
    # which should be pre-processed with BeautifulSoup;
    # otherwise, it can be very hard to find the text
    def test_can_find_full_quote_in_epub_file(self):
        FULL_CAR_QUOTE = 'The relationship between the gate and the all-important circulation of traffic sparked another debate. The attachment many Germans have to their cars has always stopped short of the American practice of tearing down cities to make way for cars, but the passion of German car lovers seems to arouse in Green-thinking Germans the same kind of suspicion that passionate patriotism does.'
        book = epub.read_epub(TEST_EPUB_BERLIN)
        section = book.get_item_with_href('text/part0011.html')
        soup = BeautifulSoup(section.get_content(), 'html.parser').get_text()
        start_index = soup.find(FULL_CAR_QUOTE)
        end_index = start_index + len(FULL_CAR_QUOTE)

    def test_can_find_partial_quote_in_epub_file(self):
        PARTIAL_QUOTE = """fundamental laws of ecology. When we include the fossil fuel energy consumed in food production, we burn 8 calories for every calorie of food we produce. That’s not a great recipe for avoiding extinction.
"""
        print(PARTIAL_QUOTE)
        title, highlight, _, section, _ = get_highlight_from_database("1fb6bc3a-7d4f-40a0-ab62-c095fa62b26a")
        path = section.split('#')[0]
        book = epub.read_epub(TEST_EPUB_BURN)
        # the OEBPS/ must be ommited - not sure why!
        section = None
        while section is None:
            print(path)
            section = book.get_item_with_href(path)
            path = "/".join(path.split("/")[1:])
        soup = BeautifulSoup(section.get_content(), 'html.parser').get_text()
        # `soup` is ALL CONTEXT; from here, one can trim 
        # start_index = soup.find(PARTIAL_QUOTE)
        # end_index = start_index + len(PARTIAL_QUOTE)
        # print(soup[start_index - 300:end_index])

    def test_can_extend_quote_backwards_until_period(self):
        PARTIAL_QUOTE = """fundamental laws of ecology. When we include the fossil fuel energy consumed in food production, we burn 8 calories for every calorie of food we produce. That’s not a great recipe for avoiding extinction.
"""
        title, highlight, _, section, _ = get_highlight_from_database("1fb6bc3a-7d4f-40a0-ab62-c095fa62b26a")
        path = section.split('#')[0]
        book = epub.read_epub(TEST_EPUB_BURN)
        # the OEBPS/ must be ommited - not sure why!
        section = None
        while section is None:
            print(path)
            section = book.get_item_with_href(path)
            path = "/".join(path.split("/")[1:])
        soup = BeautifulSoup(section.get_content(), 'html.parser').get_text()
        # `soup` is ALL CONTEXT; from here, one can trim 
        res = expand_quote(PARTIAL_QUOTE, soup, True)
        print(res)
        self.assertEqual(res,
                         """Our modern food production system violates the fundamental laws of ecology. When we include the fossil fuel energy consumed in food production, we burn 8 calories for every calorie of food we produce. That’s not a great recipe for avoiding extinction.""")


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
