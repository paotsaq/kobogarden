from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Footer, Header, OptionList, Static
from textual import events
from textual.screen import Screen
from textual.reactive import reactive
from textual.widgets.option_list import Option, Separator
from utils import (
        get_list_of_highlighted_books,
        get_all_highlights_of_book_from_database
        )
from rich.table import Table



class BookHighlightsWidget(Screen):
    def __init__(self, name: str, selected_option: Option) -> None:
        super().__init__(name)
        self.book = selected_option.id

    @staticmethod
    def highlight_generator(highlight: str, date: str) -> Table:
        table = Table(show_header=False)
        table.add_row(date.split('T')[0])
        table.add_row(highlight)
        return table

    def compose(self) -> ComposeResult:
        highlights = [self.highlight_generator(*highlight_info) for highlight_info 
                 in get_all_highlights_of_book_from_database(self.book)]
        # Store the OptionList instance as an attribute
        self.option_list = OptionList(*highlights)
        yield Header()
        yield self.option_list  # Yield the stored OptionList instance

    def on_key(self, event: events.Key) -> None:
        if event.key == "q":
            self.dismiss()

class MainScreen(App[None]):
    CSS_PATH = "option_list.tcss"

    
    def compose(self) -> ComposeResult:
        books = [Option(f'{title} by {author}', id=title) for title, author, _
                 in get_list_of_highlighted_books('./test_kobo_db.sqlite')]
        # Store the OptionList instance as an attribute
        self.option_list = OptionList(*books)
        yield Header()
        yield self.option_list  # Yield the stored OptionList instance
        yield Footer()

    def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            selected_option_index = self.option_list.highlighted
            selected_option = self.option_list._options[selected_option_index]
            self.push_screen(BookHighlightsWidget("panel", selected_option))

if __name__ == "__main__":
    MainScreen().run()
