import sqlite3
from bs4 import BeautifulSoup
from ebooklib import epub
from os import listdir
from datetime import datetime
import re

### DATABASE

TIDDLERS_PATH = '/home/apinto/paogarden/tiddlers/'
SQLITE_DB_PATH = "./"
SQLITE_DB_NAME = "test_kobo_db.sqlite"
EXISTING_IDS_FILE = "kobo highlight ids of quotes.tid"

def create_connection_to_database(
        path: str
        ) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    return conn


def get_all_highlights_of_book_from_database(
        book_name: str
        ) -> list[str]:
    """returns a list with
    full highlight content and date of highlight"""
    conn = create_connection_to_database(SQLITE_DB_PATH + SQLITE_DB_NAME)
    c = conn.cursor()
    c.execute(f"""
    SELECT
    Bookmark.Text,
    Bookmark.DateCreated,
    BookmarkID
    FROM "Bookmark"
    LEFT OUTER JOIN content
    ON (content.contentID=Bookmark.VolumeID and content.ContentType=6)
    WHERE
    content.Title="{book_name}"
    ORDER BY Bookmark.DateCreated
    """)
    content = c.fetchall()
    conn.close()
    return content


def get_highlight_from_database(
        highlight_id: str
        ) -> list[str]:
    """returns a list with
    title of book, full highlight content, date of highlight,
    start of highlight, end of highlight"""
    conn = create_connection_to_database(SQLITE_DB_PATH + SQLITE_DB_NAME)
    c = conn.cursor()
    c.execute(f"""
    SELECT
    content.title as BookTitle,
    Bookmark.Text,
    Bookmark.DateCreated,
    StartContainerPath,
    Bookmark.VolumeID
    FROM "Bookmark"
    LEFT OUTER JOIN content
    ON (content.contentID=Bookmark.VolumeID and content.ContentType=6)
    WHERE
    BookmarkID="{highlight_id}"
    """)
    # 240106: there was a bug in matching certain quotes;
    # it was due to `quote_to_expand` being preceded by whitespace.
    # the `.strip()` seems to be a fix.
    content = c.fetchall()[0]
    fixed_path = content[4].split('/')[-1]
    content = list(content[:4]) + [fixed_path]
    if fixed_path[-5:] != '.epub':
        raise FileNotFoundError
    conn.close()
    content[1] = content[1].strip()
    return content


def get_list_of_highlighted_books(
        sqlite_db_path: str
        ):
    def take_epub_file_name_from_path(path: str):
        return path.split('/')[-1]
    conn = create_connection_to_database(sqlite_db_path)
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
    WHERE content.Attribution IS NOT NULL
    """)
    results = c.fetchall()  # Fetch all results
    conn.close()
    parsed = [
            [title, author, take_epub_file_name_from_path(file)]
            for title, author, file in results
            ]
    return parsed


### PREVIOUS QUOTES

def record_in_highlight_id(highlight_id: str) -> bool:
    with open(TIDDLERS_PATH + EXISTING_IDS_FILE, "r") as file:
        return highlight_id in file.read().splitlines()


def add_highlight_id_to_record(highlight_id: str) -> None:
    """This function doesn't check whether the highlight already exists!"""
    with open(TIDDLERS_PATH + EXISTING_IDS_FILE, "a") as file:
        file.write('\n\n' + highlight_id + '\n\n')

### QUOTE HANDLING

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


def produce_highlight_tiddler_string(
        created_timestamp: str,
        tags: list,
        highlight_title: str,
        comment: str,
        highlight: str,
        quote_order: int
        ) -> str:
    return f"""created: {created_timestamp}
creator: paotsaq
modified: {created_timestamp}
modifier: paotsaq
tags: {" ".join([tag if ' ' not in tag else f'[[{tag}]]' for tag in tags])}
title: {highlight_title}
type: text/vnd.tiddlywiki
quote-order: {'0' if quote_order < 10 else ''}{str(quote_order)}

{comment}

<<<
{highlight}
<<<
"""

### BOOK TIDDLERS

def produce_book_tiddler_string(
        created_timestamp: str,
        book: str,
        author: str,
        ) -> str:
    """The function is only responsible for creating
    the book tiddler; it will be necessary to update the 
    `nbr_of_highlights` field on a separate function; by
    default, it will start at 1 (book tiddlers are created
    in the single highlight panel)"""
    return f"""created: {created_timestamp}
creator: paotsaq
modified: {created_timestamp}
modifier: paotsaq
tags: book
title: {book}
author: {author}
nbr_of_highlights: 1
type: text/vnd.tiddlywiki

\\import [tag[macro]]

<$list filter="[tag<currentTiddler>sort[quote-order]]">
   <$macrocall $name="renderTitleAndContent" tiddler=<<currentTiddler>> />
</$list>
"""

def book_tiddler_exists(book_title: str) -> bool:
    return book_title + '.tid' in listdir(TIDDLERS_PATH)

def create_book_tiddler(
        book_title: str,
        book_author: str
        ) -> None:
    formatted_now = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
    content = produce_book_tiddler_string(formatted_now, book_title, book_author)
    with open(TIDDLERS_PATH + book_title + '.tid', 'w') as file:
        file.write(content)
    
def increment_book_tiddler_highlight_number(book_title: str) -> int:
    """The function increments the book tiddler highlight number,
    but also returns the number of highlights"""
    with open(TIDDLERS_PATH + book_title + '.tid', 'r') as file:
        content = file.read()
    lines = content.splitlines()
    # NOTE the try/except block handles the weird rearrangement 
    # of the tiddler's inner structure whenever the author field
    # is changed through the TiddlyWiki frontend. 
    # solving the `AUTHOR_IS_MISSING` hardcode is not guaranteed to be a solution
    # because that might be wrong at some points too.
    try:
        NBR_OF_HIGHLIGHTS_LINE_INDEX = 7
        highlight_count = int(lines[NBR_OF_HIGHLIGHTS_LINE_INDEX].split()[1])
        lines[NBR_OF_HIGHLIGHTS_LINE_INDEX] = f'nbr_of_highlights: {highlight_count + 1}'
    except ValueError:
        NBR_OF_HIGHLIGHTS_LINE_INDEX = 5
        highlight_count = int(lines[NBR_OF_HIGHLIGHTS_LINE_INDEX].split()[1])
        lines[NBR_OF_HIGHLIGHTS_LINE_INDEX] = f'nbr_of_highlights: {highlight_count + 1}'
    with open(TIDDLERS_PATH + book_title + '.tid', 'w') as file:
        content = file.write("\n".join(lines))
    return highlight_count + 1
