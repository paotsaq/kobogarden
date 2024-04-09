from textual.app import ComposeResult
from textual.widgets import Header, OptionList  # ,Footer
from textual import events
from textual.screen import Screen
from textual.widgets.option_list import Option
from rich.table import Table
from utils.const import (
        VIM_BINDINGS,
        BOOKS_DIR
        )
from utils.database import (
        get_all_highlights_of_book_from_database,
        get_book_filename_from_book_name
        )
from utils.tiddler_handling import (
    record_in_highlight_id
)
from utils.toc_handling import (
    get_table_of_contents_from_epub,
    match_highlight_section_to_chapter
        )


class QuotesList(OptionList):
    BINDINGS = VIM_BINDINGS

    def __init__(self, *options: Option) -> None:
        super().__init__(*options)


class BookHighlightsScreen(Screen):
    """Screen responsible for displaying each books' highlights"""

    def __init__(self, name: str, selected_option: Option) -> None:
        super().__init__(name)
        self.contents_for_dismiss = [name, selected_option]
        self.book = selected_option.id
        self.highlights = get_all_highlights_of_book_from_database(self.book)
        book_path = get_book_filename_from_book_name(self.book)
        self.book_toc = get_table_of_contents_from_epub(BOOKS_DIR + book_path)

    @staticmethod
    def highlight_generator(
            highlight: str,
            date: str,
            highlight_id: str,
            container_path: str,
            book_toc: str) -> Table:
        chapter = match_highlight_section_to_chapter(container_path, book_toc)
        table = Table(show_header=False)
        table.add_row(date.split('T')[0] + ' | ' +
                      str('✅' if record_in_highlight_id(highlight_id)
                          else '❌') +
                      (' | ' + chapter if chapter else ''))
        table.add_row(highlight.strip())
        return Option(table, id=highlight_id)

    def compose(self) -> ComposeResult:
        highlights = [self.highlight_generator(*highlight_info,
                                               book_toc=self.book_toc)
                      for highlight_info in self.highlights]
        self.quotes_list = QuotesList(*highlights)
        yield Header()
        yield self.quotes_list

    def on_key(self, event: events.Key) -> None:
        if event.key == "q":
            self.dismiss()
        elif event.key == "enter":
            selected_option = self.quotes_list._options[self.quotes_list.highlighted]
            self.dismiss(['H', [self.book, selected_option]])
