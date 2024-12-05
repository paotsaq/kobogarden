from textual.app import ComposeResult
from textual.widgets import OptionList, Static, Header
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
from interface.book_metadata_modal import BookMetadataModal
from textual.binding import Binding


class QuotesList(OptionList):
    BINDINGS = VIM_BINDINGS

    def __init__(self, *options: Option) -> None:
        super().__init__(*options)


class BookHighlightsScreen(Screen):
    """Screen responsible for displaying each books' highlights"""

    BINDINGS = [
        Binding("m", "edit_metadata", "Edit Metadata", show=True),
        # ... your existing bindings ...
    ]

    def __init__(self, name: str,
                 book_option,
                 book_metadata: dict,
                 highlight_option: Option | None = None,
                 highlight_option_id: int | None = None):
        """
        Args:
            name: Screen name
            book_option: Selected book option from the list
            highlight_option: Selected highlight option from the list
        """
        super().__init__(name)
        self.book_option = book_option
        
        # Get latest metadata from TiddlerFilenameManager
        manager = TiddlerFilenameManager()
        manager.refresh_metadata()
        mapped_title, mapped_author = manager.get_mapped_metadata(book_metadata["filename"])
        
        # Use mapped values if available, otherwise use original metadata
        title = mapped_title if mapped_title is not None else book_metadata.get("title", "")
        author = mapped_author if mapped_author is not None else book_metadata.get("author", "")
        
        # Update metadata with latest info from mappings file
        self.book_metadata = {
            **book_metadata,
            "title": title,
            "author": author
        }
        
        # Set the screen's subtitle to show book info
        self.sub_title = f"{title} by {author}"
        
        logging.debug(f"Initializing BookHighlightsScreen with metadata: {self.book_metadata}")
        self.highlight_option = highlight_option
        self.highlight_option_id = highlight_option_id
        
        try:
            # Load highlights from database using filename
            self.highlights = get_all_highlights_of_book_from_database(self.book_metadata["filename"])
            if not self.highlights:
                logging.info(f"No highlights found for book: {self.book_metadata['filename']}")
                self.highlights = []
            self.book_toc = get_table_of_contents_from_epub(BOOKS_DIR + self.book_metadata["filename"])
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
                "book_metadata": self.book_metadata,
                "highlight_option": selected_highlight_option,
                "highlight_option_id": self.quotes_list.highlighted
                                }])

    async def action_edit_metadata(self) -> None:
        """Handle the metadata editing action."""
        logging.info(f"Opening metadata modal with current metadata: {self.book_metadata}")
        
        def check_modal_result(result: dict | None) -> None:
            """Handle the modal result"""
            logging.info(f"Modal callback received result: {result}")
            
            if result is not None:
                try:
                    manager = TiddlerFilenameManager()
                    manager.update_metadata_mapping(
                        original_filename=result["filename"],
                        title=result["title"],
                        author=result["author"]
                    )
                    # Update current screen's metadata
                    self.book_metadata = result
                    self.sub_title = f"{result['title']} by {result['author']}"
                    logging.info(f"Successfully updated metadata: {self.book_metadata}")
                    self.notify("Book metadata updated successfully", severity="success")
                except Exception as e:
                    logging.error(f"Failed to update metadata mapping: {str(e)}")
                    self.notify("Failed to save metadata changes", severity="error")
            else:
                logging.info("Metadata update cancelled by user")
        
        await self.app.push_screen(BookMetadataModal(self.book_metadata), check_modal_result)
