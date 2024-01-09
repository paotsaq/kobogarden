from bs4 import BeautifulSoup
from ebooklib import epub
import re
from utils.const import (
        BOOKS_DIR
        )
from utils.database import (
    get_highlight_from_database,

)


# provides the full content of the .html file
# in which a given highlight can be found. Highlights in Kobo
# will carry information about the section in which they are.
# Then, the highlight must be found inside the section
# (and the section can be quite big).
def get_full_context_from_highlight(
        book_path: str,
        section_path: str
        ) -> str:
    book = epub.read_epub(book_path)
    if not book:
        raise FileNotFoundError("The book doesn't seem to exist?")
    section = None
    i = 0
    while section is None and i < 20:
        section = book.get_item_with_href(section_path)
        section_path = "/".join(section_path.split("/")[1:])
        i += 1
    if section is None:
        return None
    soup = BeautifulSoup(section.get_content(), 'html.parser').get_text()
    return soup


# gets the paragraph that contains a sentence.
def get_book_sentence_that_matches_highlight(
        h: str,
        book_sentences: list[str]
        ) -> int:
    # NOTE this is still a very naive method ('x' in 'xyz')
    start_index, sentence = next(filter(lambda enum_tuple: h in enum_tuple[1],
                                 enumerate(book_sentences)))
    return start_index


def break_string_into_list_of_sentences(string: str):
    # pattern to break a string (soup or highlight) into a list of sentences,
    # using the period ('.') as delimiter.
    pattern = r"(?<=[.!?])\s*(?=•|\w)"
    return re.split(pattern, string)


def get_index_of_sentence_in_sentences_list(
        sentence: str,
        sentences: list[str]
        ):
    return next(filter(lambda enum_tuple: sentence in enum_tuple[1],
                       enumerate(sentences)))


# NOTE the soup is the whole context of the quote.
# this function retrieves the sentence or paragraph containing the quote,
# In the case of the first or last sentence of the highlight being incomplete,
# the function will try to get the beginning and/or end of enclosing sentence.
# FIXME it can handle the span of two paragraphs (many is still to be implemented)
def get_start_and_end_of_highlight(
        soup: str,
        highlight: str
        ) -> list[str]:

    # NOTE is this still needed?
    # # removes whitespace and newlines
    # highlight_sentences = list(filter(lambda s: s != '',
                                      # map(lambda s: s.strip(),
                                          # re.split(pattern, highlight))))

    highlight_sentences = break_string_into_list_of_sentences(highlight)
    # NOTE I feel something could be done here
    if len(highlight_sentences) == 1:
        pass

    start_of_highlight = highlight_sentences[0]

    # NOTE highlight might in a single word. check tests for
    # 'test_can_get_quote_across_two_paragraphs'
    # 'test_highlight_with_single_word_stray'
    # FIXME there should also be a test for
    # the same happening at the beginning
    end_of_highlight = highlight_sentences[-1]
    if len(end_of_highlight.split()) == 1:
        end_of_highlight = highlight_sentences[-2]

    # NOTE shouldn't soup be passed to break_string_into_list_of_sentences instead?
    # broken_soup = break_string_into_list_of_sentences(soup)
    broken_soup = soup.splitlines()
    [start_paragraph_index, start_paragraph] = (
            get_index_of_sentence_in_sentences_list(start_of_highlight,
                                                    broken_soup))
    [end_paragraph_index, end_paragraph] = (
            get_index_of_sentence_in_sentences_list(end_of_highlight,
                                                    broken_soup))

    if (end_paragraph_index < start_paragraph_index):
        # something went terribly wrong; communicate the error
        raise Exception("end_paragraph_index < start_paragraph_index")

    # more than one paragraph
    if start_paragraph_index != end_paragraph_index:
        start_book_sentences = break_string_into_list_of_sentences(start_paragraph)
        start_index = get_book_sentence_that_matches_highlight(start_of_highlight,
                                                               start_book_sentences)
        end_book_sentences = break_string_into_list_of_sentences(end_paragraph)
        end_index = get_book_sentence_that_matches_highlight(end_of_highlight,
                                                             end_book_sentences)
        # concatenate the start_of_highlight paragraph,
        # any paragraphs in between,
        # and then the end_of_highlight paragraph
        return ([" ".join(start_book_sentences[start_index:]),
                 "\n\n",
                 # middle_book_paragraphs,
                 " ".join(end_book_sentences[:end_index + 1])])

    else:
        book_sentences = break_string_into_list_of_sentences(start_paragraph)
        start_index = get_book_sentence_that_matches_highlight(start_of_highlight,
                                                               book_sentences)
        end_index = get_book_sentence_that_matches_highlight(end_of_highlight,
                                                             book_sentences)
        return (book_sentences[start_index:end_index + 1])


# the function provides more context for a given highlight.
# it will return `amount_of_sentences` before or after the highlight
def expand_found_highlight(
    highlight_to_expand: list[str],
    soup: list[str],
    amount_of_sentences: int,
    backwards: bool,
        ) -> list[str]:
    # decide whether to look for first or last sentence of highlight
    anchor = 0 if backwards else -1
    broken_soup = break_string_into_list_of_sentences(soup)
    highlight_location = broken_soup.index(highlight_to_expand[anchor])
    return (broken_soup[highlight_location - amount_of_sentences:highlight_location]
            if backwards
            else broken_soup[highlight_location + 1:highlight_location + 1 + amount_of_sentences])


def get_context_indices_for_highlight_display(
        context: str,
        highlight: str
        ):
    highlight = highlight
    start_index = context.find(highlight)
    end_index = start_index + len(highlight)
    return start_index, end_index


def get_highlight_context_from_id(
        highlight_id: str,
        ) -> list[str]:
    title, highlight, _, section, book_path = (
            get_highlight_from_database(highlight_id))
    soup = get_full_context_from_highlight(BOOKS_DIR + book_path, section.split('#')[0])
    paragraphs = get_start_and_end_of_highlight(soup, highlight)
    return paragraphs
