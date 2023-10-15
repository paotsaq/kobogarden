from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.containers import Grid 
from textual.widgets import Footer, Header, OptionList, Input, Button, Label
from textual import events
from textual.screen import Screen
from textual.reactive import reactive
from textual.widgets.option_list import Option
from utils import (
        get_list_of_highlighted_books,
        get_all_highlights_of_book_from_database,
        get_highlight_from_database,
        get_context_indices_for_highlight_display,
        get_full_context_from_highlight,
        produce_tiddler_string,
        record_in_highlight_id,
        add_highlight_id_to_record
        )
from rich.table import Table
from rich.text import Text
from datetime import datetime

BOOKS_PATH = ""
PAOGARDEN_PATH = "/users/alexj/paogarden/tiddlers/"


class MainScreen(App[None]):
    """Application starts here. Main panel will have an OptionList
    object, with each available book for highlights.
    This class is responsible for handling the different screens."""
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
        # NOTE maybe some enums / different types (instead of 
        # hardcoded single-letter strings?)
        def check_highlights_panel_quit(options: list | None):
            """Helper function to determine outcomes of different screens"""
            next_screen, content = options
            if next_screen == 'H':
                self.push_screen(SingleHighlightsScreen("panel", content))
            elif next_screen == 'C':
                self.push_screen(ConfirmHighlightScreen("confirm", *content))

        # a book has been chosen on the main panel
        if event.key == "enter":
            selected_option_index = self.option_list.highlighted
            selected_option = self.option_list._options[selected_option_index]
            self.push_screen(BookHighlightsWidget("panel", selected_option),
                             check_highlights_panel_quit)

class BookHighlightsWidget(Screen):
    """Screen responsible for displaying each books' highlights"""
    def __init__(self, name: str, selected_option: Option) -> None:
        super().__init__(name)
        self.book = selected_option.id

    @staticmethod
    def highlight_generator(highlight: str, date: str, highlight_id: str) -> Table:
        table = Table(show_header=False)
        table.add_row(date.split('T')[0] + ' | ' +
                      str('✅' if record_in_highlight_id(highlight_id)
                           else '❌'))
        table.add_row(highlight)
        return Option(table, id=highlight_id)

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
        elif event.key == "enter":
            selected_option_index = self.option_list.highlighted
            selected_option = self.option_list._options[selected_option_index]
            self.dismiss(['H', [self.book, selected_option]])


class SingleHighlightWidget(Widget, can_focus=True):
    start = reactive(0)
    end = reactive(0)
    early_context = reactive(0)
    later_context = reactive(0)
    quote = reactive("")

    def __init__(self, highlight: Option, soup: str, start: int, end: int) -> None:
        super().__init__()
        self.highlight = highlight
        self.soup = soup
        self.start = start
        self.end = end
        self.early_context = self.start - 300
        self.later_context = self.end + 300
        self.styles.background = "purple"
        self.styles.width = "60%"
        self.styles.height = "40%"
        self.styles.padding = 2
        self.quote = self.soup[self.start:self.end].strip()

    @staticmethod
    def highlight_generator(highlight: str, date: str) -> Table:
        table = Table(show_header=False)
        table.add_row(date.split('T')[0])
        table.add_row(highlight)
        return table

    def render(self) -> Text:
        text = Text()
        text.append(f"...{self.soup[self.early_context:self.start].strip()}", style='#828282')
        text.append(f" {self.quote} ", style='bold')
        text.append(f"{self.soup[self.end:self.later_context].strip()}...", style='#828282')
        return text


class SingleHighlightsScreen(Screen):
    CSS_PATH = "option_list.tcss"

    def __init__(self, name: str, content: tuple[str, Option]) -> None:
        super().__init__(name)
        self.book, self.highlight = content

    def compose(self) -> ComposeResult:
        _, highlight, _, section = get_highlight_from_database(self.highlight.id)
        soup = get_full_context_from_highlight('./burn.epub', section.split('#')[0])
        start, end = get_context_indices_for_highlight_display(soup, highlight)
        self.highlight_widget = SingleHighlightWidget(self.highlight, soup, start, end)

        self.highlight_notes =  Input(classes='highlight_input',
                    placeholder='further notes about the quote?')
        self.highlight_title = Input(classes='highlight_input',
                    placeholder='title for the quote tiddler?')
        self.highlight_tags = Input(classes='highlight_input',
                    placeholder='space separated tags?')
        yield self.highlight_widget       
        yield self.highlight_notes
        yield self.highlight_title
        yield self.highlight_tags
        yield Header()
        yield Footer()
        yield Button("Create tiddler!", 
                     variant="success")

    def on_key(self, event: events.Key) -> None:
        if event.key == "q":
            self.dismiss()
        elif event.key == "h":
            self.query_one(SingleHighlightWidget).start -= 1
        elif event.key == "k":
            self.query_one(SingleHighlightWidget).end -= 1
        elif event.key == "j":
            self.query_one(SingleHighlightWidget).start += 1
        elif event.key == "l":
            self.query_one(SingleHighlightWidget).end += 1
        elif event.key == "J":
            self.query_one(SingleHighlightWidget).start += 50
        elif event.key == "K":
            self.query_one(SingleHighlightWidget).end += 50
        elif event.key == "b":
            self.query_one(SingleHighlightWidget).early_context += 50
        elif event.key == "f":
            self.query_one(SingleHighlightWidget).later_context += 50
        elif event.key == "B":
            self.query_one(SingleHighlightWidget).early_context -= 50
        elif event.key == "F":
            self.query_one(SingleHighlightWidget).later_context -= 50

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # TODO this should be better handled
        if self.highlight_title.value == "":
            return
        # Remove the last 3 digits of microseconds
        formatted_now = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        tiddler = produce_tiddler_string(
                formatted_now,
                self.book + ' ' + self.highlight_tags.value,
                self.highlight_title.value,
                self.highlight_notes.value,
                self.highlight_widget.quote
                )
        with open(PAOGARDEN_PATH + self.highlight_title.value + '.tid', "w") as file:
            file.write(tiddler)

        add_highlight_id_to_record(self.highlight.id)




if __name__ == "__main__":
    MainScreen().run()
