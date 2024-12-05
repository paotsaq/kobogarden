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
    OPTIONS_CSS_PATH,
    VIM_BINDINGS
        )
from utils.database import (
    get_list_of_highlighted_books,
    )
from utils.logging import logging


class BookList(OptionList):
    BINDINGS = VIM_BINDINGS

    def __init__(self, *options: Option) -> None:
        super().__init__(*options)


# class BookOption(Option):

    # def __init__(self) -> None:
        # super().__init__()

    # def __repr__(self):
        # return


class MainScreen(App[None]):
    """Application starts here. Main panel will have an OptionList
    object, with each available book for highlights.
    This class is responsible for handling the different screens."""

    CSS_PATH = OPTIONS_CSS_PATH

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  
        self.current_book = None

    def compose(self) -> ComposeResult:
        books = [Option(f'{title} by {author}', id=title) for title, author, _
                 in get_list_of_highlighted_books(DATABASE_PATH)]

        # Store the OptionList instance as an attribute
        # self.option_list = BookList(*books)
        self.book_list = BookList(*books)
        yield Header()
        yield self.book_list
        yield Footer()

    def on_key(self, event: events.Key) -> None:
        def check_highlights_panel_quit(options: list | None):
            """Helper function to determine outcomes of different screens"""
            next_screen, content = options
            logging.debug(f"screen_callback_content:\n{content}")
            if next_screen == 'H':
                self.push_screen(SingleHighlightsScreen("single_highlight", **content),
                                 check_highlights_panel_quit)
            # move from specific highlight to book highlights screen
            elif next_screen == 'B':
                self.push_screen(BookHighlightsScreen("book_highlights", **content),
                                 check_highlights_panel_quit)

        # a book has been chosen on the main panel
        if event.key == "enter":
            selected_book_index = self.book_list.highlighted
            selected_book_option = self.book_list._options[selected_book_index]
            self.push_screen(BookHighlightsScreen("book_highlights",
                                                  selected_book_option),
                             check_highlights_panel_quit)
