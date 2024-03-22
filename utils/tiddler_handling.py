from os import listdir
from datetime import datetime
from utils.const import (
    TIDDLERS_PATH,
    EXISTING_IDS_FILE
        )


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
creator: kobogarden
created: {created_timestamp}
modifier: kobogarden
modified: {created_timestamp}
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


# 240322 - adds a book-quote tiddler by default 
def produce_highlight_tiddler_string(
        created_timestamp: str,
        tags: list,
        highlight_title: str,
        comment: str,
        highlight: str,
        quote_order: int
        ) -> str:
    return f"""created: {created_timestamp}
creator: kobogarden
created: {created_timestamp}
modifier: kobogarden
modified: {created_timestamp}
tags: {" ".join(["book-quote"] + [tag if ' ' not in tag else f'[[{tag}]]'
                                      for tag in tags])}
title: {highlight_title}
type: text/vnd.tiddlywiki
quote-order: {'0' if quote_order < 10 else ''}{str(quote_order)}

{comment}

<<<
{highlight}
<<<
"""


def record_in_highlight_id(highlight_id: str) -> bool:
    with open(TIDDLERS_PATH + EXISTING_IDS_FILE, "r") as file:
        return highlight_id in file.read().splitlines()


def add_highlight_id_to_record(highlight_id: str) -> None:
    """This function doesn't check whether the highlight already exists!"""
    with open(TIDDLERS_PATH + EXISTING_IDS_FILE, "a") as file:
        file.write('\n\n' + highlight_id + '\n\n')
