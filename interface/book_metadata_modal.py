from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.widgets import Button, Input, Label, Static
from textual.binding import Binding
from utils.logging import logging

class BookMetadataModal(ModalScreen[dict]):
    """Modal for editing book metadata."""
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "submit", "Submit", show=True)
    ]

    def __init__(self, book_metadata: dict) -> None:
        super().__init__()
        self.book_metadata = book_metadata

    def compose(self) -> ComposeResult:
        with Vertical(id="metadata-dialog"):
            yield Label("Edit Book Metadata")
            yield Static("Title:")
            yield Input(
                value=self.book_metadata.get("title", ""),
                id="title-input"
            )
            yield Static("Author:")
            yield Input(
                value=self.book_metadata.get("author", ""),
                id="author-input"
            )
            with Vertical(id="dialog-buttons"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", variant="error", id="cancel")

    def action_submit(self) -> None:
        """Handle the submit action (Save button or Enter key)."""
        new_metadata = dict(
            title=self.query_one("#title-input").value,
            author=self.query_one("#author-input").value,
            filename=self.book_metadata["filename"]
        )
        logging.info(f"Modal: Submitting metadata via action: {new_metadata}")
        self.dismiss(new_metadata)

    def action_cancel(self) -> None:
        """Handle the cancel action (Cancel button or Escape key)."""
        logging.info("Modal: Cancelling metadata update via action")
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Map button presses to actions"""
        if event.button.id == "save":
            self.action_submit()
        else:
            self.action_cancel()

    def on_input_submitted(self) -> None:
        """Handle Enter key in input fields"""
        self.action_submit() 