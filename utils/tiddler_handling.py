from os import listdir
from datetime import datetime
from utils.const import (
    TIDDLERS_PATH,
    EXISTING_IDS_FILE
        )


def produce_fhl_tiddler_string(
        created_timestamp: str,
        book: str,
        ) -> str:
    """The function is only responsible for creating
    the full highlights list tiddler;
    """
    return f"""created: {created_timestamp}
creator: kobogarden
created: {created_timestamp}
modifier: kobogarden
modified: {created_timestamp}
tags: fhl
title: fhl-{book}
type: text/vnd.tiddlywiki

\\import [tag[macro]]

<$list filter="[tag[book-quote]tag[{book}]sort[quote-order]]">
   <$macrocall $name="renderClickableTitle" tiddler=<<currentTiddler>> />
</$list>
"""


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

//[the notes from the book were retrieved with [[kobogarden]], with the purpose of aiding to create a map of the ideas the book left me. The full list of book highlights can be found [[here|fhl-{book}]].]//

<div style="float: left; margin: 0 40px 8px 0;
                  width: 30%;
                  justify-content: space-between;
                  align-content: space-between;
                  max-width: 200px">
<$image source={{!!book-cover-tiddler}}/>
</div>
"""


def book_tiddler_exists(book_title: str) -> bool:
    return book_title + '.tid' in listdir(TIDDLERS_PATH)


def create_book_tiddler(
        book_title: str,
        book_author: str
        ) -> None:
    formatted_now = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
    book_content = produce_book_tiddler_string(formatted_now, book_title, book_author)
    fhl_content = produce_fhl_tiddler_string(formatted_now, book_title)
    with open(TIDDLERS_PATH + book_title + '.tid', 'w') as file:
        file.write(book_content)
    print("Created book tiddler: " + book_title)
    with open(TIDDLERS_PATH + 'fhl-' + book_title + '.tid', 'w') as file:
        file.write(fhl_content)
    print("Created fhl tiddler: " + book_title)


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
