from datetime import datetime
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Footer, Header, OptionList, Input, Button
from textual import events
from textual.screen import Screen
from textual.reactive import reactive
from textual.widgets.option_list import Option
from rich.table import Table
from rich.text import Text
from utils.const import (
    OPTIONS_CSS_PATH,
    TIDDLERS_PATH,
        )
from utils.database import (
        get_highlight_from_database,
        )
from utils.tiddler_handling import (
    produce_highlight_tiddler_string,
)
from utils.highlight_handling import (
        expand_quote,
        get_full_context_from_highlight,
        get_context_indices_for_highlight_display,
        get_start_and_end_of_highlight,
        )


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

    @staticmethod
    def highlight_generator(highlight: str, date: str) -> Table:
        table = Table(show_header=False)
        table.add_row(date.split('T')[0])
        table.add_row(highlight)
        return table

    def render(self) -> Text:
        text = Text()
        self.quote = self.soup[self.start:self.end].strip()
        text.append(f"...{self.soup[self.early_context:self.start].strip()}", style='#828282')
        text.append(f" {self.soup[self.start:self.end].strip()} ", style='bold')
        text.append(f"{self.soup[self.end:self.later_context].strip()}...", style='#828282')
        return text


class SingleHighlightsScreen(Screen):
    CSS_PATH = OPTIONS_CSS_PATH

    def __init__(self, name: str, content: tuple[str, Option]) -> None:
        super().__init__(name)
        self.book, self.highlight = content

    def compose(self) -> ComposeResult:
        _, highlight, _, section, book_file_name = get_highlight_from_database(self.highlight.id)
        soup = get_full_context_from_highlight(book_file_name, section.split('#')[0])
        # NOTE this is problematic
        start, end = get_context_indices_for_highlight_display(soup, highlight)
        self.highlight_widget = SingleHighlightWidget(self.highlight, soup, start, end)

        self.highlight_notes = Input(classes='highlight_input',
                                     placeholder='further notes about the quote?')
        self.highlight_title = Input(classes='highlight_input',
                                     placeholder='title for the quote tiddler?')
        self.highlight_tags = Input(classes='highlight_input',
                                    placeholder='space separated tags?')
        yield self.highlight_widget
        yield self.highlight_title
        yield self.highlight_notes
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
        elif event.key == "j":
            self.query_one(SingleHighlightWidget).start += 1
        elif event.key == "H":
            self.query_one(SingleHighlightWidget).start -= 50
        elif event.key == "J":
            self.query_one(SingleHighlightWidget).start += 50
        elif event.key == "k":
            self.query_one(SingleHighlightWidget).end -= 1
        elif event.key == "K":
            self.query_one(SingleHighlightWidget).end -= 50
        elif event.key == "l":
            self.query_one(SingleHighlightWidget).end += 1
        elif event.key == "L":
            self.query_one(SingleHighlightWidget).end += 50
        elif event.key == "b":
            self.query_one(SingleHighlightWidget).early_context += 50
        elif event.key == "B":
            self.query_one(SingleHighlightWidget).early_context -= 50
        elif event.key == "f":
            self.query_one(SingleHighlightWidget).later_context += 50
        elif event.key == "F":
            self.query_one(SingleHighlightWidget).later_context -= 50

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # TODO this should be better handled
        if self.highlight_title.value == "":
            return

        # Access or create book tiddler, and retrieve the `highlight_order`
        if book_tiddler_exists(self.book):
            highlight_order = increment_book_tiddler_highlight_number(self.book)
        else:
            create_book_tiddler(self.book, "AUTHOR_IS_MISSING")
            highlight_order = 1

        # Remove the last 3 digits of microseconds
        formatted_now = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]

        # Creates the tiddler string
        tiddler = produce_highlight_tiddler_string(
                formatted_now,
                [self.book] + self.highlight_tags.value.split(),
                self.highlight_title.value,
                self.highlight_notes.value,
                self.highlight_widget.quote,
                highlight_order
                )

        # Writes the new tiddler file
        with open(TIDDLERS_PATH + self.highlight_title.value + '.tid', "w") as file:
            file.write(tiddler)

        add_highlight_id_to_record(self.highlight.id)
