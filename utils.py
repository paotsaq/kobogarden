import sqlite3
from bs4 import BeautifulSoup
from ebooklib import epub
from os import listdir
from datetime import datetime

### DATABASE

TIDDLERS_PATH = '/users/alexj/paogarden/tiddlers/'
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
    content = c.fetchall()[0]
    fixed_path = content[4].split('/')[-1]
    content = tuple(list(content[:4]) + [fixed_path])
    if fixed_path[-5:] != '.epub':
        raise FileNotFoundError 
    conn.close()
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

def expand_quote(
    quote_to_expand: str,
    context: str,
    backwards: bool,
    cons: int = 200
        ) -> str:
    start_index = context.find(quote_to_expand[:-1])
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


def get_full_context_from_highlight(
        book_path: str,
        section_path: str
        ) -> str:
    book = epub.read_epub(book_path)
    if not book:
        raise FileNotFoundError("The book doesn't seem to exist?")
    section = None
    while section is None:
        section = book.get_item_with_href(section_path)
        section_path = "/".join(section_path.split("/")[1:])
    soup = BeautifulSoup(section.get_content(), 'html.parser').get_text()
    return soup


def get_context_indices_for_highlight_display(
        context: str,
        highlight: str
        ):
    start_index = context.find(highlight)
    end_index = start_index + len(highlight)
    return start_index, end_index


def produce_highlight_tiddler_string(
        created_timestamp: str,
        tags: str,
        highlight_title: str,
        comment: str,
        highlight: str,
        quote_order: int
        ) -> str:
    return f"""created: {created_timestamp}
creator: paotsaq
modified: {created_timestamp}
modifier: paotsaq
tags: {tags}
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
    NBR_OF_HIGHLIGHTS_LINE_INDEX = 5
    with open(TIDDLERS_PATH + book_title + '.tid', 'r') as file:
        content = file.read()
    lines = content.splitlines()
    print(lines)
    highlight_count = int(lines[NBR_OF_HIGHLIGHTS_LINE_INDEX].split()[1])
    print(highlight_count)
    lines[NBR_OF_HIGHLIGHTS_LINE_INDEX] = f'nbr_of_highlights: {highlight_count + 1}'
    with open(TIDDLERS_PATH + book_title + '.tid', 'w') as file:
        content = file.write("\n".join(lines))
    return highlight_count + 1
