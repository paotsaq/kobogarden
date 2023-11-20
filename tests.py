import unittest
from utils import (
        create_connection_to_database,
        get_highlight_from_database,
        expand_quote,
        get_full_context_from_highlight,
        get_list_of_highlighted_books,
        get_all_highlights_of_book_from_database
        )
import sqlite3

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
        conn.close()

    # returns many fields from the query
    def test_can_retrieve_jane_eyre_highlight_content_from_ID(self):
        rows = get_highlight_from_database("94ace0c6-b132-48b1-b0d9-1ef0e38db1ed")
        self.assertEqual(rows[0], 'Jane Eyre: An Autobiography')
        self.assertEqual(rows[1], '\nI had made no noise: he had not eyes behind—could his shadow feel?')
        self.assertEqual(rows[2], '2023-08-30T18:09:48.000')
        self.assertEqual(rows[3], 'OEBPS/6048514455528670785_1260-h-25.htm.html#point(/1/4/1/21:1)')
        self.assertEqual(rows[4], 'jane-eyre.epub')

    def test_can_retrieve_berlin_highlight_content_from_ID(self):
        rows = get_highlight_from_database("f27d6696-d59a-4cb1-a329-310fd17d6eea")
        self.assertEqual(rows[0], 'The Ghosts of Berlin: Confronting German History in the Urban Landscape')
        self.assertEqual(rows[1], 'The relationship between the gate and the all-important circulation of traffic sparked another debate. The attachment many Germans have to their cars has always stopped short of the American practice of tearing down cities to make way for cars, but the passion of German car lovers seems to arouse in Green-thinking Germans the same kind of suspicion that passionate patriotism does.')
        self.assertEqual(rows[2], '2023-08-30T06:13:56.000')
        self.assertEqual(rows[3], 'text/part0011.html#point(/1/4/192/3:147)')
        self.assertEqual(rows[4], 'The Ghosts of Berlin_ Confronting German History in the Urban Landscape.epub')
        self.quote = rows[1]
        self.quote_location = rows[3]

    def test_can_retrieve_a_list_of_books_which_have_highlights(self):
        res = get_list_of_highlighted_books('./test_kobo_db.sqlite')
        self.assertIn(['The Ghosts of Berlin: Confronting German History in the Urban Landscape', 'Brian Ladd', '- The Ghosts of Berlin_ Confronting German History in the Urban Landscape.epub'], res)

    def test_can_provide_all_highlights_from_a_given_book(self):
        res = get_all_highlights_of_book_from_database('The Ghosts of Berlin: Confronting German History in the Urban Landscape')
        self.assertEqual(len(res), 26)


class TestingFindingQuoteInEpubFiles(unittest.TestCase):
    # epubs are fundamentally HTML files,
    # which should be pre-processed with BeautifulSoup;
    # otherwise, it can be very hard to find the text

    # if there is an exact quote, the `get_full_context_from_highlight`
    # can provide a full quote
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

    def test_can_extend_quote_forwards_until_next_period(self):
        PARTIAL_QUOTE = """When the molecules in a pound of nitroglycerin (chemical formula: 4C3H5N3O9) are broken into nitrogen (N2), water (H2O), carbon monoxide (CO), and oxygen (O2) during detonation, it violently releases enough energy (730 kilocalories)"""
        FULL_QUOTE = """When the molecules in a pound of nitroglycerin (chemical formula: 4C3H5N3O9) are broken into nitrogen (N2), water (H2O), carbon monoxide (CO), and oxygen (O2) during detonation, it violently releases enough energy (730 kilocalories) to launch a 165-pound man two and a half miles straight up into the sky (which would be work) or vaporize him (which would be heat), or some combination of the two. This brings us to our last point about energy: it can be converted among its many forms—kinetic energy, heat, work, chemical energy, and so on—but it can never be lost."""
        title, highlight, _, section, _ = get_highlight_from_database("c71f3857-162f-43c2-b783-d63eb63b6957")
        soup = get_full_context_from_highlight(TEST_EPUB_BURN, section.split('#')[0])
        # `soup` is ALL CONTEXT; from here, one can trim 
        res = expand_quote(PARTIAL_QUOTE, soup, False)
        res = expand_quote(res, soup, False)
        self.assertEqual(res, FULL_QUOTE)


if __name__ == '__main__':
    unittest.main()
