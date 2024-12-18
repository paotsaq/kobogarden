import unittest
import sqlite3
from ebooklib import epub
from datetime import datetime
from utils.database import (
        create_connection_to_database,
        get_highlight_from_database,
        get_all_highlights_of_book_from_database,
        get_list_of_highlighted_books,
        )
from utils.tiddler_handling import (
    produce_highlight_tiddler_string,
    produce_book_tiddler_string,
    create_book_tiddler
)
from utils.highlight_handling import (
        get_full_context_from_highlight,
        get_start_and_end_of_highlight,
        expand_found_highlight,
        )
from utils.const import (
    SQLITE_DB_PATH,
    SQLITE_DB_NAME,
)
from utils.toc_handling import (
    get_table_of_contents_from_epub,
    retrieve_clean_href,
    get_dict_of_href_and_title_from_toc,
    match_highlight_section_to_chapter,
    get_previous_chapter_from_section
)

TEST_BOOKS_DIR = 'test_books/'
TEST_EPUB_JANEEYRE = 'jane-eyre.epub'
TEST_EPUB_BERLIN = 'berlin.epub'
TEST_EPUB_BURN = 'burn.epub'
TEST_EPUB_HOWTO = 'howto.epub'
TEST_EPUB_SCATTERED = 'scattered_minds.epub'
TEST_EPUB_APRENDENDO = 'aprendendo.epub'
TEST_EPUB_SHALLOWS = 'shallows.epub'
TEST_EPUB_STRANGERS = 'strangers.epub'


class TestingKoboDatabase(unittest.TestCase):
    def test_can_open_kobo_database(self):
        conn = create_connection_to_database(SQLITE_DB_PATH + SQLITE_DB_NAME)
        self.assertIsNotNone(conn)
        c = conn.cursor()
        self.assertTrue(type(c) == sqlite3.Cursor)
        conn.close()

    # returns many fields from the query
    def test_can_retrieve_jane_eyre_highlight_content_from_ID(self):
        rows = get_highlight_from_database("94ace0c6-b132-48b1-b0d9-1ef0e38db1ed")
        self.assertEqual(rows[0], 'Jane Eyre: An Autobiography')
        self.assertEqual(rows[1], 'Charlotte Brontë')
        self.assertEqual(rows[2], 'I had made no noise: he had not eyes behind—could his shadow feel?')
        self.assertEqual(rows[3], '2023-08-30T18:09:48.000')
        self.assertEqual(rows[4], 'OEBPS/6048514455528670785_1260-h-25.htm.html#point(/1/4/1/21:1)')
        self.assertEqual(rows[5], 'jane-eyre.epub')

    def test_can_retrieve_berlin_highlight_content_from_ID(self):
        rows = get_highlight_from_database("f27d6696-d59a-4cb1-a329-310fd17d6eea")
        self.assertEqual(rows[0], 'The Ghosts of Berlin: Confronting German History in the Urban Landscape')
        self.assertEqual(rows[1], 'Brian Ladd')
        self.assertEqual(rows[2], 'The relationship between the gate and the all-important circulation of traffic sparked another debate. The attachment many Germans have to their cars has always stopped short of the American practice of tearing down cities to make way for cars, but the passion of German car lovers seems to arouse in Green-thinking Germans the same kind of suspicion that passionate patriotism does.')
        self.assertEqual(rows[3], '2023-08-30T06:13:56.000')
        self.assertEqual(rows[4], 'text/part0011.html#point(/1/4/192/3:147)')
        self.assertEqual(rows[5], '- The Ghosts of Berlin_ Confronting German History in the Urban Landscape.epub')

    def test_can_retrieve_a_list_of_books_which_have_highlights(self):
        res = get_list_of_highlighted_books('./test_kobo_db.sqlite')
        self.assertIn(['The Ghosts of Berlin: Confronting German History in the Urban Landscape', 'Brian Ladd', '- The Ghosts of Berlin_ Confronting German History in the Urban Landscape.epub'], res)

    def test_can_provide_all_highlights_from_a_given_book(self):
        res = get_all_highlights_of_book_from_database('The Ghosts of Berlin: Confronting German History in the Urban Landscape')
        self.assertEqual(len(res), 26)


# epubs are fundamentally HTML files,
# which should be pre-processed with BeautifulSoup;
# otherwise, it can be very hard to find the text

# if there is an exact quote, the `get_full_context_from_highlight`
# can provide a full quote
class TestingFindingQuoteInEpubFiles(unittest.TestCase):

    # the highlight is well-delimited (no partial sentences before or after).
    def test_can_find_simple_full_quote_in_epub_file(self):
        QUOTE = 'The relationship between the gate and the all-important circulation of traffic sparked another debate.'
        title, _, highlight, _, section, _ = get_highlight_from_database("1fb6bc3a-7d4f-40a0-ab62-c095fa62b26a")
        soup = get_full_context_from_highlight(TEST_BOOKS_DIR + TEST_EPUB_BERLIN, 'text/part0011.html')
        self.assertIsNotNone(soup)
        result = " ".join(get_start_and_end_of_highlight(soup, QUOTE))
        self.assertEqual(result, QUOTE)

    # the highlight is well-delimited (no partial sentences before or after),
    # but ends in a question mark.
    def test_can_find_simple_full_quote_in_epub_file_with_punctuation(self):
        HIGHLIGHT_ID = "871ca40f-3d58-4fff-be19-400e700bdad6"
        QUOTE = """When people long for some kind of escape, it’s worth asking: What would “back to the land” mean if we understood the land to be where we are right now?"""
        title, _, highlight, _, section, _ = (x := get_highlight_from_database(HIGHLIGHT_ID))
        soup = get_full_context_from_highlight(TEST_BOOKS_DIR + TEST_EPUB_HOWTO, section.split('#')[0])
        self.assertIsNotNone(soup)
        result = " ".join(get_start_and_end_of_highlight(soup, QUOTE))
        self.assertEqual(result, QUOTE)
        
    # the highlight is partial at the beginning.
    # in this case, the first sentence is presented in its complete form.
    def test_can_extend_quote_backwards_until_period(self):
        PARTIAL_QUOTE = """fundamental laws of ecology."""
        FULL_QUOTE = """Our modern food production system violates the fundamental laws of ecology."""
        title, _, highlight, _, section, _ = get_highlight_from_database("1fb6bc3a-7d4f-40a0-ab62-c095fa62b26a")
        # NOTE: the OEBPS/ must be ommited - not sure why!
        soup = get_full_context_from_highlight(TEST_BOOKS_DIR + TEST_EPUB_BURN, section.split('#')[0])
        self.assertIsNotNone(soup)
        result = " ".join(get_start_and_end_of_highlight(soup, PARTIAL_QUOTE))
        self.assertEqual(result, FULL_QUOTE)

    # the highlight is partial at the end.
    # in this case, the last sentence is presented in its complete form.
    def test_can_extend_quote_forwards_until_period(self):
        PARTIAL_QUOTE = """When the molecules in a pound of nitroglycerin (chemical formula: 4C3H5N3O9) are broken into nitrogen (N2), water (H2O), carbon monoxide (CO), and oxygen (O2) during detonation, it violently releases enough energy (730 kilocalories)"""
        FULL_QUOTE = """When the molecules in a pound of nitroglycerin (chemical formula: 4C3H5N3O9) are broken into nitrogen (N2), water (H2O), carbon monoxide (CO), and oxygen (O2) during detonation, it violently releases enough energy (730 kilocalories) to launch a 165-pound man two and a half miles straight up into the sky (which would be work) or vaporize him (which would be heat), or some combination of the two."""
        title, _, highlight, _, section, _ = get_highlight_from_database("c71f3857-162f-43c2-b783-d63eb63b6957")
        soup = get_full_context_from_highlight(TEST_BOOKS_DIR + TEST_EPUB_BURN, section.split('#')[0])
        result = " ".join(get_start_and_end_of_highlight(soup, PARTIAL_QUOTE))
        self.assertEqual(result, FULL_QUOTE)

    # the highlight is partial at the beginning and end.
    # in this case, both beginning and end are retrieved.
    # sentence is now in its complete form
    def test_can_extend_quote_forwards_and_backwards_until_period(self):
        PARTIAL_QUOTE = """pound of nitroglycerin (chemical formula: 4C3H5N3O9) are broken into nitrogen (N2), water (H2O), carbon monoxide (CO), and oxygen (O2) during detonation, it violently releases enough energy (730 kilocalories)"""
        FULL_QUOTE = """When the molecules in a pound of nitroglycerin (chemical formula: 4C3H5N3O9) are broken into nitrogen (N2), water (H2O), carbon monoxide (CO), and oxygen (O2) during detonation, it violently releases enough energy (730 kilocalories) to launch a 165-pound man two and a half miles straight up into the sky (which would be work) or vaporize him (which would be heat), or some combination of the two."""
        title, _, highlight, _, section, _ = get_highlight_from_database("c71f3857-162f-43c2-b783-d63eb63b6957")
        soup = get_full_context_from_highlight(TEST_BOOKS_DIR + TEST_EPUB_BURN, section.split('#')[0])
        result = " ".join(get_start_and_end_of_highlight(soup, PARTIAL_QUOTE))
        self.assertEqual(result, FULL_QUOTE)

    # the highlight not only is malformed, it also spans line-breaks.
    # the '4' at the end of a sentence is a bummer,
    # but it came in the Kobo highlight.
    # Added a special case in the function for that.
    def test_can_get_quote_across_two_paragraphs(self):
        """"""
        FULL_QUOTE = """Such “nothings” cannot be tolerated because they cannot be used or appropriated, and provide no deliverables. (Seen in this context, Trump’s desire to defund the National Endowment for the Arts comes as no surprise.) In the early twentieth century, the surrealist painter Giorgio de Chirico foresaw a narrowing horizon for activities as “unproductive” as observation. He wrote:

In the face of the increasingly materialist and pragmatic orientation of our age…it would not be eccentric in the future to contemplate a society in which those who live for the pleasures of the mind will no longer have the right to demand their place in the sun. The writer, the thinker, the dreamer, the poet, the metaphysician, the observer…he who tries to solve a riddle or to pass judgement will become an anachronistic figure, destined to disappear from the face of the earth like the ichthyosaur and the mammoth."""
        title, _, highlight, _, section, book_path = get_highlight_from_database("b22af57c-2b8c-494f-ac99-96fa698f1dac")
        soup = get_full_context_from_highlight(TEST_BOOKS_DIR + TEST_EPUB_HOWTO, section.split('#')[0])
        result = get_start_and_end_of_highlight(soup, highlight)
        self.assertEqual(" ".join(result), FULL_QUOTE)

    def test_can_extend_quote_forwards_until_next_period(self):
        PARTIAL_QUOTE = """When the molecules in a pound of nitroglycerin (chemical formula: 4C3H5N3O9) are broken into nitrogen (N2), water (H2O), carbon monoxide (CO), and oxygen (O2) during detonation, it violently releases enough energy (730 kilocalories)"""
        FIRST_FOUND_QUOTE = """When the molecules in a pound of nitroglycerin (chemical formula: 4C3H5N3O9) are broken into nitrogen (N2), water (H2O), carbon monoxide (CO), and oxygen (O2) during detonation, it violently releases enough energy (730 kilocalories) to launch a 165-pound man two and a half miles straight up into the sky (which would be work) or vaporize him (which would be heat), or some combination of the two."""
        title, _, highlight, _, section, _ = get_highlight_from_database("c71f3857-162f-43c2-b783-d63eb63b6957")
        soup = get_full_context_from_highlight(TEST_BOOKS_DIR + TEST_EPUB_BURN, section.split('#')[0])
        found_highlight = get_start_and_end_of_highlight(soup, PARTIAL_QUOTE)
        self.assertEqual(" ".join(found_highlight), FIRST_FOUND_QUOTE)
        expanded_highlight = expand_found_highlight(found_highlight, soup, 1, False)
        FULL_QUOTE = " ".join([FIRST_FOUND_QUOTE,
                               """This brings us to our last point about energy: it can be converted among its many forms—kinetic energy, heat, work, chemical energy, and so on—but it can never be lost."""])
        self.assertEqual(" ".join([FIRST_FOUND_QUOTE, " ".join(expanded_highlight)]), FULL_QUOTE)

    def test_can_extend_quote_backwards_until_next_period(self):
        PARTIAL_QUOTE = """When the molecules in a pound of nitroglycerin (chemical formula: 4C3H5N3O9) are broken into nitrogen (N2), water (H2O), carbon monoxide (CO), and oxygen (O2) during detonation, it violently releases enough energy (730 kilocalories)"""
        title, _, highlight, _, section, _ = get_highlight_from_database("c71f3857-162f-43c2-b783-d63eb63b6957")
        soup = get_full_context_from_highlight(TEST_BOOKS_DIR + TEST_EPUB_BURN, section.split('#')[0])
        found_highlight = get_start_and_end_of_highlight(soup, PARTIAL_QUOTE)
        FIRST_FOUND_QUOTE = """When the molecules in a pound of nitroglycerin (chemical formula: 4C3H5N3O9) are broken into nitrogen (N2), water (H2O), carbon monoxide (CO), and oxygen (O2) during detonation, it violently releases enough energy (730 kilocalories) to launch a 165-pound man two and a half miles straight up into the sky (which would be work) or vaporize him (which would be heat), or some combination of the two."""
        self.assertEqual(" ".join(found_highlight), FIRST_FOUND_QUOTE)
        expanded_highlight = expand_found_highlight(found_highlight, soup, 1, True)
        FULL_QUOTE = " ".join(["""The bonds that hold molecules together can store chemical energy, which gets released when the molecules break apart.""", FIRST_FOUND_QUOTE])
        self.assertEqual(" ".join([" ".join(expanded_highlight), FIRST_FOUND_QUOTE]), FULL_QUOTE)

    # highlight is well-formed, but ends with a single stray word.
    # eg: "Well-formed highlight. But then. Oops"
    # in this case, the code would look for `Oops`,
    # but this pattern (as it only has one word) might occur elsewhere in the text.
    # to make the search more robust, the code would look for `But then. Oops`
    def test_highlight_with_single_word_stray(self):
        HIGHLIGHT_ID = "302e8612-9b65-43b0-b871-e9943038afc6"
        FULL_QUOTE = "The shock of self-recognition many adults experience on learning about ADD is both exhilarating and painful. It gives coherence, for the first time, to humiliations and failures, to plans unfulfilled and promises unkept, to gusts of manic enthusiasm that consume themselves in their own mad dance, leaving emotional debris in their wake, to the seemingly limitless disorganization of activities, of brain, car, desk, room."
        title, _, highlight, _, section, book_path = get_highlight_from_database(HIGHLIGHT_ID)
        soup = get_full_context_from_highlight(TEST_BOOKS_DIR + TEST_EPUB_SCATTERED, section.split('#')[0])
        self.assertNotEqual(soup, None)
        result = " ".join(get_start_and_end_of_highlight(soup, highlight))
        self.assertEqual(result, FULL_QUOTE)


    def test_weird_symbols_in_quote(self):
        HIGHLIGHT_ID = "f96e9093-fd56-400c-93f6-102c4ade243f"
        title, _, highlight, _, section, book_path = get_highlight_from_database(HIGHLIGHT_ID)
        soup = get_full_context_from_highlight(TEST_BOOKS_DIR + 'trip.epub',
                                               section.split('#')[0])
        self.assertNotEqual(soup, None)
        result = " ".join(get_start_and_end_of_highlight(soup, highlight))
        self.assertEqual(result, """• For reasons examined throughout this book, I’ve gradually realized that sustained, conscious effort is required—or at least strongly self-suggested—for me to not drift toward meaninglessness, depression, disempowering forms of resignation, and bleak ideologies like existentialism.""")


class TestingCreationOfHighlightTiddler(unittest.TestCase):

    # 11/21 tags were failing when the book title had spaces.
    # ideally, the `produce_highlight_tiddler_string` will
    # enclose any given tag (including book title) with double square brackets.
    def test_can_create_highlight_tiddler(self):
        self.maxDiff = None
        # Remove the last 3 digits of microseconds
        formatted_now = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        book = 'How to do Nothing'
        title = 'this is just a test tiddler'
        comment = 'I don\'t know what to say'
        highlight = 'really, this is just a test tiddler'

        # Creates the tiddler string
        tiddler = produce_highlight_tiddler_string(
                formatted_now,
                [book, 'test', 'another test'],
                title,
                comment,
                highlight,
                1
                )
        result = f"""created: {formatted_now}
creator: kobogarden
created: {formatted_now}
modifier: kobogarden
modified: {formatted_now}
tags: book-quote [[{book}]] test [[another test]]
title: {title}
chapter: 
type: text/vnd.tiddlywiki
quote-order: 01

{comment}

<<<
{highlight}
<<<
"""
        self.assertEqual(tiddler, result)


# 24/02/01 - realised chapter information about each book would be nice.
class TestingBookTableOfContents(unittest.TestCase):
    def test_can_get_table_of_contents_for_a_given_book(self):
        book_toc = get_table_of_contents_from_epub(TEST_BOOKS_DIR + TEST_EPUB_HOWTO)
        self.assertIsNotNone(book_toc)

    def test_can_get_table_of_contents_for_another_given_book(self):
        book_toc = get_table_of_contents_from_epub(TEST_BOOKS_DIR + TEST_EPUB_SCATTERED)
        self.assertIsNotNone(book_toc)

    # on SCATTERED_MINDS, book chapters come with chapter number.
    def test_can_retrieve_chapter_info_from_toc(self):
        HIGHLIGHT_ID = "e56c7386-951f-4b60-b500-f5ceff2c8777"
        title, _, highlight, _, section, path = (x := get_highlight_from_database(HIGHLIGHT_ID))
        book_toc = get_table_of_contents_from_epub(TEST_BOOKS_DIR + TEST_EPUB_SCATTERED)
        self.assertEqual(match_highlight_section_to_chapter(section, book_toc), '10 The Footprints of Infancy')

    # HOWTO has the best mapping so far, and this test ensures any further changes
    # will not break the mapping;
    def test_can_create_full_toc_from_howto_book(self):
        book_toc = get_table_of_contents_from_epub(TEST_BOOKS_DIR + TEST_EPUB_HOWTO)
        self.assertEqual(
            get_dict_of_href_and_title_from_toc(book_toc),
            {'xhtml/Odel_9781612197500_epub3_cvi_r1.xhtml': 'Cover', 'xhtml/Odel_9781612197500_epub3_tp_r1.xhtml': 'Title Page', 'xhtml/Odel_9781612197500_epub3_cop_r1.xhtml': 'Copyright', 'xhtml/Odel_9781612197500_epub3_ded_r1.xhtml': 'Dedication', 'xhtml/Odel_9781612197500_epub3_toc_r1.xhtml': 'Contents', 'xhtml/Odel_9781612197500_epub3_itr_r1.xhtml': 'Introduction: Surviving Usefulness', 'xhtml/Odel_9781612197500_epub3_c01_r1.xhtml': 'Chapter 1: The Case for Nothing', 'xhtml/Odel_9781612197500_epub3_c02_r1.xhtml': 'Chapter 2: The Impossibility of Retreat', 'xhtml/Odel_9781612197500_epub3_c03_r1.xhtml': 'Chapter 3: Anatomy of a Refusal', 'xhtml/Odel_9781612197500_epub3_c04_r1.xhtml': 'Chapter 4: Exercises in Attention', 'xhtml/Odel_9781612197500_epub3_c05_r1.xhtml': 'Chapter 5: Ecology of Strangers', 'xhtml/Odel_9781612197500_epub3_c06_r1.xhtml': 'Chapter 6: Restoring the Grounds for Thought', 'xhtml/Odel_9781612197500_epub3_con_r1.xhtml': 'Conclusion: Manifest Dismantling', 'xhtml/Odel_9781612197500_epub3_ack_r1.xhtml': 'Acknowledgments', 'xhtml/Odel_9781612197500_epub3_end_r1.xhtml': 'Notes'})

    def test_can_match_highlight_with_a_chapter(self):
        HIGHLIGHT_ID = "871ca40f-3d58-4fff-be19-400e700bdad6"
        title, _, highlight, _, section, path = (x := get_highlight_from_database(HIGHLIGHT_ID))
        book_toc = get_table_of_contents_from_epub(TEST_BOOKS_DIR + TEST_EPUB_HOWTO)
        self.assertEqual(match_highlight_section_to_chapter(section, book_toc), 'Introduction: Surviving Usefulness')


    # 24/04/17: SHALLOWS has some issues with mapping chapters.
    def test_can_create_full_toc_from_shallows_book(self):
        book_toc = get_table_of_contents_from_epub(TEST_BOOKS_DIR + TEST_EPUB_SHALLOWS)
        self.assertEqual(
            get_dict_of_href_and_title_from_toc(book_toc),
            {'The_Shallows_split_009.html': 'THE WATCHDOG AND THE THIEF', 'The_Shallows_split_010.html': 'HAL AND ME', 'The_Shallows_split_011.html': 'THE VITAL PATHS', 'The_Shallows_split_012.html': 'on what the brain thinks about when it thinks about itself', 'The_Shallows_split_013.html': 'TOOLS OF THE MIND', 'The_Shallows_split_015.html': 'THE DEEPENING PAGE', 'The_Shallows_split_016.html': 'on lee de forest and his amazing audion', 'The_Shallows_split_017.html': 'A MEDIUM OF THE MOST GENERAL NATURE', 'The_Shallows_split_018.html': 'THE VERY IMAGE OF A BOOK', 'The_Shallows_split_019.html': 'THE JUGGLER’S BRAIN', 'The_Shallows_split_021.html': 'on the buoyancy of IQ scores', 'The_Shallows_split_022.html': 'THE CHURCH OF GOOGLE', 'The_Shallows_split_024.html': 'SEARCH, MEMORY', 'The_Shallows_split_025.html': 'on the writing of this book', 'The_Shallows_split_026.html': 'A THING LIKE ME', 'The_Shallows_split_027.html': 'HUMAN ELEMENTS', 'The_Shallows_split_029.html': 'Notes', 'The_Shallows_split_030.html': 'Further Reading', 'The_Shallows_split_031.html': 'Acknowledgments'})

    def test_can_retrieve_the_preceding_chapter(self):
        SECTION = "The_Shallows_split_014.html#point(/1/4/4/8/1:446)"
        clean_section = retrieve_clean_href(SECTION)
        book_toc = get_table_of_contents_from_epub(TEST_BOOKS_DIR + TEST_EPUB_SHALLOWS)
        toc_dict = get_dict_of_href_and_title_from_toc(book_toc)
        self.assertEqual(get_previous_chapter_from_section(clean_section, toc_dict), 'The_Shallows_split_013.html')

    # 24/04/17: SHALLOWS has some issues with mapping chapters.
    # the following highlight comes from 'The_Shallows_split_014.html#point(/1/4/4/8/1:446)';
    # but the chapter is not in the `.epub` toc file;
    # I'm not sure whether this will repeat with other books.
    # A solution could be to map the highlight with no chapter to the preceding chapter.
    def test_can_map_shallows_highlight_to_chapter(self):
        HIGHLIGHT_ID = "a3c65f89-bfd4-49b5-a92c-3f2fb1542229"
        title, _, highlight, _, section, path = (x := get_highlight_from_database(HIGHLIGHT_ID))
        book_toc = get_table_of_contents_from_epub(TEST_BOOKS_DIR + TEST_EPUB_SHALLOWS)
        self.assertEqual(match_highlight_section_to_chapter(section, book_toc), 'TOOLS OF THE MIND')

    # 24/08/08: there have been issues with other chapters in books
    def test_can_map_strangers_highlight_to_chapter(self):
        HIGHLIGHT_ID = "458ea2c3-f589-431e-a10d-e03de57adeac"
        title, _, highlight, _, section, path = (x := get_highlight_from_database(HIGHLIGHT_ID))
        book_toc = get_table_of_contents_from_epub(TEST_BOOKS_DIR + TEST_EPUB_STRANGERS)
        self.assertEqual(match_highlight_section_to_chapter(section, book_toc), 'Prologue: Rachel: “Someone better than me”')

    # 
    def test_can_map_aprendendo_highlight_to_chapter(self):
        HIGHLIGHT_ID = "edaa00fc-4a15-4c86-99d4-f9176e3fdacf"
        title, _, highlight, _, section, path = (x := get_highlight_from_database(HIGHLIGHT_ID))
        book_toc = get_table_of_contents_from_epub(TEST_BOOKS_DIR + TEST_EPUB_APRENDENDO)
        parsed_dict = get_dict_of_href_and_title_from_toc(book_toc)
        self.assertEqual(match_highlight_section_to_chapter(section, book_toc), 'Prologue: Rachel: “Someone better than me”')





if __name__ == '__main__':
    unittest.main()
