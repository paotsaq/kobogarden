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
from utils.logging import logging


class QuotesList(OptionList):
    BINDINGS = VIM_BINDINGS

    def __init__(self, *options: Option) -> None:
        super().__init__(*options)


class BookHighlightsScreen(Screen):
    """Screen responsible for displaying each books' highlights"""

    def __init__(self, name: str, book_option: str = None, highlight_option: str = None, highlight_option_id: int = None) -> None:
        super().__init__(name)
        self.book_option = book_option
        self.highlight_option = highlight_option
        self.highlight_option_id = highlight_option_id
        logging.debug(f"options are: \n{self.book_option}\n{self.highlight_option}")

        self.book = self.book_option.id
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
        logging.debug(f"am on compose screen!")
        if self.highlight_option_id:
            self.quotes_list.highlighted = self.highlight_option_id
        yield Header()
        yield self.quotes_list

    def on_key(self, event: events.Key) -> None:
        if event.key == "q":
            self.dismiss()
        elif event.key == "enter":
            selected_highlight_option = self.quotes_list._options[self.quotes_list.highlighted]
            logging.debug(f"highlighted option is {self.quotes_list.highlighted}")
            logging.debug(f"SELECTED_HIGHL_OPTION IS (on book screen)\n{selected_highlight_option}")
            self.dismiss(['H', {
                "book_option": self.book_option,
                "highlight_option": selected_highlight_option,
                "highlight_option_id": self.quotes_list.highlighted
                                }])
