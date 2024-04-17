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
    # takes the line corresponding to the nbr_of_highlights information
    index, line = next(filter(lambda pair: 'nbr_of_highlights' in pair[1],
                       enumerate(lines)))
    new_highlight_count = int(line.split()[1]) + 1
    new_lines = (lines[:index] +
                 [f'nbr_of_highlights: {new_highlight_count}'] +
                 lines[index + 1:])
    with open(TIDDLERS_PATH + book_title + '.tid', 'w') as file:
        content = file.write("\n".join(new_lines))
    return new_highlight_count


# 240322 - adds a book-quote tiddler by default
def produce_highlight_tiddler_string(
        created_timestamp: str,
        tags: list,
        highlight_title: str,
        comment: str,
        highlight: str,
        quote_order: int,
        chapter: str = ""
        ) -> str:
    return f"""created: {created_timestamp}
creator: kobogarden
created: {created_timestamp}
modifier: kobogarden
modified: {created_timestamp}
tags: {" ".join(["book-quote"] + [tag if ' ' not in tag else f'[[{tag}]]'
                                      for tag in tags])}
title: {highlight_title}
chapter: {chapter}
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
