import unittest
from utils import (
        create_connection_to_database,
        get_highlight_from_database,
        expand_quote,
        get_full_context_from_highlight
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
        soup = get_full_context_from_highlight(TEST_EPUB_BERLIN, 'text/part0011.html')
        start_index = soup.find(FULL_CAR_QUOTE)
        end_index = start_index + len(FULL_CAR_QUOTE)
        self.assertEqual(FULL_CAR_QUOTE, soup[start_index:end_index])

    def test_can_extend_quote_backwards_until_period(self):
        PARTIAL_QUOTE = """fundamental laws of ecology. When we include the fossil fuel energy consumed in food production, we burn 8 calories for every calorie of food we produce. That’s not a great recipe for avoiding extinction."""
        FULL_QUOTE = """Our modern food production system violates the fundamental laws of ecology. When we include the fossil fuel energy consumed in food production, we burn 8 calories for every calorie of food we produce. That’s not a great recipe for avoiding extinction."""
        title, highlight, _, section, _ = get_highlight_from_database("1fb6bc3a-7d4f-40a0-ab62-c095fa62b26a")
        # the OEBPS/ must be ommited - not sure why!
        soup = get_full_context_from_highlight(TEST_EPUB_BURN, section.split('#')[0])
        res = expand_quote(PARTIAL_QUOTE, soup, True)
        self.assertEqual(res, FULL_QUOTE)

    def test_can_extend_quote_forwards_until_period(self):
        PARTIAL_QUOTE = """When the molecules in a pound of nitroglycerin (chemical formula: 4C3H5N3O9) are broken into nitrogen (N2), water (H2O), carbon monoxide (CO), and oxygen (O2) during detonation, it violently releases enough energy (730 kilocalories)"""
        FULL_QUOTE = """When the molecules in a pound of nitroglycerin (chemical formula: 4C3H5N3O9) are broken into nitrogen (N2), water (H2O), carbon monoxide (CO), and oxygen (O2) during detonation, it violently releases enough energy (730 kilocalories) to launch a 165-pound man two and a half miles straight up into the sky (which would be work) or vaporize him (which would be heat), or some combination of the two."""
        title, highlight, _, section, _ = get_highlight_from_database("c71f3857-162f-43c2-b783-d63eb63b6957")
        soup = get_full_context_from_highlight(TEST_EPUB_BURN, section.split('#')[0])
        # `soup` is ALL CONTEXT; from here, one can trim 
        res = expand_quote(PARTIAL_QUOTE, soup, False)
        self.assertEqual(res, FULL_QUOTE)


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
