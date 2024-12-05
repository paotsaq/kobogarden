from textual.app import ComposeResult
from textual.widgets import OptionList, Static
from textual import events
from textual.screen import Screen
from textual.widgets.option_list import Option
from rich.table import Table
from utils.const import (
        VIM_BINDINGS,
        BOOKS_DIR,
        TIDDLERS_PATH
        )
from utils.database import (
        BookNotFoundError,
        get_all_highlights_of_book_from_database
        )
from utils.tiddler_handling import (
    record_in_highlight_id,
    TiddlerFilenameManager
)
from utils.toc_handling import (
    get_table_of_contents_from_epub,
    match_highlight_section_to_chapter
        )
from utils.logging import logging
from interface.book_metadata_panel import BookMetadataModal


class QuotesList(OptionList):
    BINDINGS = VIM_BINDINGS

    def __init__(self, *options: Option) -> None:
        super().__init__(*options)


class BookHighlightsScreen(Screen):
    """Screen responsible for displaying each books' highlights"""

    BINDINGS = [
        ("m", "configure_metadata", "Configure Metadata"),
        # ... your existing bindings ...
    ]

    def __init__(self, name: str, book_option, book_metadata: dict, check_quit_callback=None):
        """
        Args:
            name: Screen name
            book_option: Selected book option from the list
            check_quit_callback: Optional callback for checking quit conditions
        """
        super().__init__(name)
        self.book_option = book_option
        self.check_quit_callback = check_quit_callback
        self.book_metadata = book_metadata
        logging.debug(f"Initializing BookHighlightsScreen with metadata: {book_metadata}")
        self.highlight_option_id = None
        
        try:
            # Load highlights from database
            self.highlights = get_all_highlights_of_book_from_database(self.book_metadata["title"])
            if not self.highlights:
                logging.info(f"No highlights found for book: {self.book_metadata['title']}")
                self.highlights = []
            self.book_toc = get_table_of_contents_from_epub(self.book_metadata["filename"])
        except BookNotFoundError as e:
            logging.error(f"Book not found: {str(e)}")
            self.original_filename = None
            self.highlights = []
            self.notify("Book not found in database", severity="error")
        except Exception as e:
            logging.error(f"Error loading highlights: {str(e)}")
            self.highlights = []
            self.notify("Error loading highlights", severity="error")

    @staticmethod
    def highlight_generator(
            highlight: str,
            date: str,
            highlight_id: str,
            container_path: str,
            book_toc: str) -> Table:
        if highlight:
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
        if self.highlight_option_id:
            self.quotes_list.highlighted = self.highlight_option_id
        yield Header()
        yield self.quotes_list

    def on_key(self, event: events.Key) -> None:
        if event.key == "q":
            self.dismiss()
        elif event.key == "enter":
            selected_highlight_option = self.quotes_list._options[self.quotes_list.highlighted]
            self.dismiss(['H', {
                "book_option": self.book_option,
                "highlight_option": selected_highlight_option,
                "highlight_option_id": self.quotes_list.highlighted
                                }])
