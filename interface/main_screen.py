from textual import events
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, OptionList
from textual.widgets.option_list import Option
from interface.book_highlights_screen import BookHighlightsScreen
from interface.single_highlight_screen import (
    SingleHighlightsScreen,
        )
from utils.const import (
    DATABASE_PATH,
    OPTIONS_CSS_PATH
        )
from utils.database import (
    get_list_of_highlighted_books,
    )


class MainScreen(App[None]):
    """Application starts here. Main panel will have an OptionList
    object, with each available book for highlights.
    This class is responsible for handling the different screens."""

    CSS_PATH = OPTIONS_CSS_PATH

    def compose(self) -> ComposeResult:
        books = [Option(f'{title} by {author}', id=title) for title, author, _
                 in get_list_of_highlighted_books(DATABASE_PATH)]

        # Store the OptionList instance as an attribute
        self.option_list = OptionList(*books)
        yield Header()
        yield self.option_list  # Yield the stored OptionList instance
        yield Footer()

    def on_key(self, event: events.Key) -> None:
        # NOTE maybe some enums / different types (instead of
        # hardcoded single-letter strings?)
        def check_highlights_panel_quit(options: list | None):
            """Helper function to determine outcomes of different screens"""
            next_screen, content = options
            if next_screen == 'H':
                self.push_screen(SingleHighlightsScreen("single_highlight", content))
            # move from specific highlight to book highlights screen
            elif next_screen == 'B':
                self.push_screen(BookHighlightsScreen("book_highlights", content),
                                 check_highlights_panel_quit)

        # a book has been chosen on the main panel
        if event.key == "enter":
            selected_option_index = self.option_list.highlighted
            selected_option = self.option_list._options[selected_option_index]
            self.push_screen(BookHighlightsScreen("book_highlights", selected_option),
                             check_highlights_panel_quit)
