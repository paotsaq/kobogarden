from textual.app import ComposeResult
from textual.widgets import Header, OptionList  # ,Footer
from textual import events
from textual.screen import Screen
from textual.widgets.option_list import Option
from rich.table import Table
from utils.database import (
        get_all_highlights_of_book_from_database,
        )
from utils.tiddler_handling import (
    record_in_highlight_id
)

class QuotesList(OptionList):



class BookHighlightsScreen(Screen):
    """Screen responsible for displaying each books' highlights"""

    def __init__(self, name: str, selected_option: Option) -> None:
        super().__init__(name)
        self.contents_for_dismiss = [name, selected_option]
        self.book = selected_option.id

    @staticmethod
    def highlight_generator(
            highlight: str,
            date: str,
            highlight_id: str) -> Table:
        table = Table(show_header=False)
        table.add_row(date.split('T')[0] + ' | ' +
                      str('✅' if record_in_highlight_id(highlight_id)
                          else '❌'))
        table.add_row(highlight.strip())
        return Option(table, id=highlight_id)

    def compose(self) -> ComposeResult:
        highlights = [self.highlight_generator(*highlight_info)
                      for highlight_info
                      in get_all_highlights_of_book_from_database(self.book)]
        # Store the OptionList instance as an attribute
        self.quotes_list = OptionList(*highlights)
        yield Header()
        yield self.option_list  # Yield the stored OptionList instance

    def on_key(self, event: events.Key) -> None:
        if event.key == "q":
            self.dismiss()
        elif event.key == "enter":
            selected_option_index = self.option_list.highlighted
            selected_option = self.option_list._options[selected_option_index]
            self.dismiss(['H', [self.book, selected_option]])
