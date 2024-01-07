from bs4 import BeautifulSoup
from ebooklib import epub
import re
from utils.const import (
    BOOKS_DIR
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
    book = epub.read_epub(BOOKS_DIR + book_path)
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


# NOTE the soup is the whole context of the quote.
# this function retrieves the paragraph containing the quote,
# but I haven't yet accounted for quotes spanning multiple paragraphs.
# Also, the first or last sentence of the highlight might be incomplete.
def get_start_and_end_of_highlight(
        soup: str,
        highlight: str
        ) -> list[str]:

    def get_book_sentence_that_matches_highlight(
            h: str,
            book_sentences: list[str]
            ) -> list[int, str]:
        # gets the paragraph that contains a sentence.
        # NOTE this is still a very naive method ('x' in 'xyz')
        start_index, highlight_sentence_start = next(filter(lambda enum_tuple: h in enum_tuple[1],
                                                            enumerate(book_sentences)))
        return start_index, highlight_sentence_start

    # pattern to break a string (soup or highlight) into a list of sentences,
    # using the period ('.') as delimiter.
    pattern = r"(?<=\.)\s*(?=\w)"
    highlight_sentences = re.split(pattern, highlight)
    # # removes whitespace and newlines
    # highlight_sentences = list(filter(lambda s: s != '',
                                      # map(lambda s: s.strip(),
                                          # re.split(pattern, highlight))))

    start_of_highlight = highlight_sentences[0]

    # NOTE highlight ends in a single word. check tests for
    # 'test_can_get_quote_across_two_paragraphs'
    # 'test_highlight_with_single_word_stray'
    end_of_highlight = highlight_sentences[-1]
    if len(end_of_highlight.split()) == 1:
        end_of_highlight = highlight_sentences[-2]

    [start_paragraph_index, start_paragraph] = next(filter(lambda enum_tuple: start_of_highlight in enum_tuple[1],
                                                                enumerate(soup.splitlines())))
    [end_paragraph_index, end_paragraph] = next(filter(lambda enum_tuple: end_of_highlight in enum_tuple[1],
                                                       enumerate(soup.splitlines())))

    if (end_paragraph_index < start_paragraph_index):
        # something went terribly wrong; communicate the error
        raise Exception("end_paragraph_index < start_paragraph_index")

    # more than one paragraph
    if start_paragraph_index != end_paragraph_index:
        start_book_sentences = re.split(pattern, start_paragraph)
        start_index, _ = get_book_sentence_that_matches_highlight(start_of_highlight, start_book_sentences)
        end_book_sentences = re.split(pattern, end_paragraph)
        end_index, _ = get_book_sentence_that_matches_highlight(end_of_highlight, end_book_sentences)
        # concatenate the start_of_highlight paragraph,
        # any paragraphs in between,
        # and then the end_of_highlight paragraph
        return ("\n\n".join([" ".join(start_book_sentences[start_index:]),
                             # middle_book_paragraphs,
                             " ".join(end_book_sentences[:end_index + 1])]))

    else:
        book_sentences = re.split(pattern, start_paragraph)
        start_index, _ = get_book_sentence_that_matches_highlight(start_of_highlight, book_sentences)
        end_index, _ = get_book_sentence_that_matches_highlight(end_of_highlight, book_sentences)
        return (" ".join(book_sentences[start_index:end_index + 1]))


def expand_quote(
    quote_to_expand: str,
    context: str,
    backwards: bool,
    cons: int = 200
        ) -> str:
    quote_to_expand = quote_to_expand
    start_index = context.find(quote_to_expand[:-1])
    if start_index == -1:
        # NOTE THIS IS JUST A QUICKFIX
        start_index = context.find(quote_to_expand[:70])
        if start_index == -1:
            print("Could not find context!")
            return ""
    end_index = start_index + len(quote_to_expand)
    if backwards:
        new_index = context[start_index - cons:start_index].rfind('.')
        if new_index == -1:
            return expand_quote(quote_to_expand, context, backwards, cons + 200)
        new_quote = context[start_index - cons + new_index + 1:end_index].strip()
    else:
        new_index = context[start_index:end_index + cons].rfind('.')
        if new_index == -1:
            return expand_quote(quote_to_expand, context, backwards, cons + 200)
        new_quote = context[start_index:start_index + new_index + 1].strip()
    return new_quote


def get_context_indices_for_highlight_display(
        context: str,
        highlight: str
        ):
    highlight = highlight
    start_index = context.find(highlight)
    end_index = start_index + len(highlight)
    return start_index, end_index
