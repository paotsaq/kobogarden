from ebooklib import epub
import re
from utils.const import (
        BOOKS_DIR
        )
from utils.logging import logging
from utils.epub_validation import (
    get_full_context_from_highlight,
    )
from utils.database import (
    get_highlight_from_database,
    )
from urllib.parse import unquote


def get_index_of_sentence_in_sentences_list(
        h: str,
        book_sentences: list[str]
        ) -> int:
    # NOTE this is still a very naive method ('x' in 'xyz')
    start_index, sentence = next(filter(lambda enum_tuple: h in enum_tuple[1],
                                 enumerate(book_sentences)))
    return start_index, sentence


def break_string_into_list_of_sentences(string: str):
    # pattern to break a string (soup or highlight) into a list of sentences,
    # using the period ('.') and other punctiation as delimiter.
    pattern = r"(?<=[.!?])\s*(?=•|\w)"
    return re.split(pattern, string)



# NOTE the soup is the whole context of the quote.
# this function retrieves the sentence or paragraph containing the quote,
# In the case of the first or last sentence of the highlight being incomplete,
# the function will try to get the beginning and/or end of enclosing sentence.
# FIXME it can handle the span of two paragraphs (many is still to be implemented)
def get_start_and_end_of_highlight(
        soup: str,
        highlight: str
        ) -> list[str]:
    highlight_sentences = break_string_into_list_of_sentences(highlight)
    broken_soup = break_string_into_list_of_sentences(soup)
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

    [match_start_index, _] = (
            get_index_of_sentence_in_sentences_list(start_of_highlight,
                                                    broken_soup))
    [match_end_index, _] = (
            get_index_of_sentence_in_sentences_list(end_of_highlight,
                                                    broken_soup))

    return broken_soup[match_start_index:match_end_index + 1]


# provides the highlight with the minimum surrounding context
# ie. if the original highlight was an incomplete sentence,
# it will extend to the beginning and/or end of sentence.
def get_highlight_context_from_id(
        highlight_id: str,
        ) -> list[str]:
    title, _, highlight, _, section, book_path = (
            get_highlight_from_database(highlight_id))
    soup = get_full_context_from_highlight(BOOKS_DIR + book_path, section.split('#')[0])
    if soup is None:
        return
    paragraphs = get_start_and_end_of_highlight(soup, highlight)
    return paragraphs


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
    try: 
        highlight_location = broken_soup.index(highlight_to_expand[anchor])
        return (broken_soup[highlight_location - amount_of_sentences:highlight_location]
                if backwards
                else broken_soup[highlight_location + 1:highlight_location + 1 + amount_of_sentences])
    except IndexError:
        return highlight_to_expand

