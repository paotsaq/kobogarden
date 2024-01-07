from datetime import datetime
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Footer, Header, Input, Button
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
    add_highlight_id_to_record,
    produce_highlight_tiddler_string,
    book_tiddler_exists,
    create_book_tiddler,
    increment_book_tiddler_highlight_number
)
from utils.highlight_handling import (
        get_full_context_from_highlight,
        get_context_indices_for_highlight_display,
        get_start_and_end_of_highlight,
        get_highlight_context_from_id
        )


class TiddlerInformationWidget(Widget, can_focus=True):
    def __init__(self, book_name: str, highlight: Option) -> None:
        super().__init__()

    def compose(self) -> ComposeResult:
        self.highlight_notes = Input(classes='highlight_input',
                                     placeholder='further notes about the quote?')
        self.highlight_title = Input(classes='highlight_input',
                                     placeholder='title for the quote tiddler?')
        self.highlight_tags = Input(classes='highlight_input',
                                    placeholder='space separated tags?')
        yield self.highlight_title
        yield self.highlight_notes
        yield self.highlight_tags
        yield Button("Create tiddler!",
                     variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # TODO this should be better handled
        if self.highlight_title.value == "":
            return

        return
        # # Access or create book tiddler, and retrieve the `highlight_order`
        # if book_tiddler_exists(self.book):
            # highlight_order = increment_book_tiddler_highlight_number(self.book)
        # else:
            # create_book_tiddler(self.book, "AUTHOR_IS_MISSING")
            # highlight_order = 1

        # # Remove the last 3 digits of microseconds
        # formatted_now = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]

        # # Creates the tiddler string
        # tiddler = produce_highlight_tiddler_string(
                # formatted_now,
                # [self.book] + self.highlight_tags.value.split(),
                # self.highlight_title.value,
                # self.highlight_notes.value,
                # self.highlight_widget.quote,
                # highlight_order
                # )

        # # Writes the new tiddler file
        # with open(TIDDLERS_PATH + self.highlight_title.value + '.tid', "w") as file:
            # file.write(tiddler)

        # add_highlight_id_to_record(self.highlight.id)


class SingleHighlightWidget(Widget, can_focus=True):
    start = reactive(0)
    end = reactive(0)
    early_context = reactive(0)
    later_context = reactive(0)
    quote = reactive("")

    def __init__(self, book_name: str, highlight: Option) -> None:
        super().__init__()
        self.book_name = book_name
        self.highlight = highlight
        self.highlight_id = highlight.id
        self.styles.background = "purple"
        self.styles.width = "60%"
        self.styles.height = "80%"
        self.styles.padding = 2

    def render(self) -> Text:
        text = Text()
        self.quote = get_highlight_context_from_id(self.highlight_id)
        # text.append(f"...{self.soup[self.early_context:self.start].strip()}", style='#828282')
        # text.append(f" {self.soup[self.start:self.end].strip()} ", style='bold')
        # text.append(f"{self.soup[self.end:self.later_context].strip()}...", style='#828282')
        text.append(self.quote)
        return text


class SingleHighlightsScreen(Screen):
    CSS_PATH = OPTIONS_CSS_PATH

    def __init__(self, name: str, content: tuple[str, Option]) -> None:
        super().__init__(name)
        self.content = content
        self.styles.layout = 'horizontal'

    def compose(self) -> ComposeResult:
        self.highlight_widget = SingleHighlightWidget(*self.content)
        self.tiddler_info_widget = TiddlerInformationWidget(*self.content)

        yield self.highlight_widget
        yield self.tiddler_info_widget
        yield Header()
        yield Footer()

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

