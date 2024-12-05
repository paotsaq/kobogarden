from textual.widgets import Input, Static, Button
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from pathlib import Path
from utils.const import (
    TIDDLERS_PATH,
    )
from utils.database import get_book_details_from_book_name, BookNotFoundError, DatabaseError
import logging

class BookMetadataModal(ModalScreen):
    """Modal screen for editing book metadata"""
    
    def __init__(self, book_name: str, original_filename: str):
        """
        Args:
            book_name: The clean book title from the database
            original_filename: The actual filename of the epub
        """
        super().__init__()
        self.original_filename = original_filename
        
        try:
            # Query using the book_name, not the filename
            _, self.current_title, self.current_author = get_book_details_from_book_name(book_name)
        except (BookNotFoundError, DatabaseError) as e:
            logging.error(f"Error getting book details: {str(e)}")
            self.notify(str(e), severity="error")
            self.current_title = book_name
            self.current_author = ""

    def compose(self):
        yield Vertical(
            Static("Book Metadata Configuration", classes="header"),
            Vertical(
                Static("Original filename:"),
                Static(self.original_filename, classes="filename"),
                Static("Title:"),
                Input(value=self.current_title, id="title_input"),
                Static("Author:"),
                Input(value=self.current_author, id="author_input"),
                Horizontal(
                    Button("Save", variant="primary", id="save"),
                    Button("Cancel", variant="default", id="cancel"),
                    classes="buttons"
                ),
                classes="form"
            ),
            classes="metadata-modal"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            new_title = self.query_one("#title_input").value
            new_author = self.query_one("#author_input").value
            
            # Create mapping file if different from original
            if (new_title != self.current_title or 
                new_author != self.current_author):
                mapping_filename = f"{new_title} ({new_author}) <- {self.original_filename}"
                Path(TIDDLERS_PATH / mapping_filename).touch()
            
            self.dismiss(True)
        else:
            self.dismiss(False) 