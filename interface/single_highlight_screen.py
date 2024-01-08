from datetime import datetime
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Footer, Header, Input, Button
from textual import events
from textual.screen import Screen
from textual.reactive import reactive
from textual.containers import VerticalScroll, Vertical
from textual.widgets.option_list import Option
from rich.table import Table
from rich.text import Text
from utils.const import (
    OPTIONS_CSS_PATH,
    TIDDLERS_PATH,
    BOOKS_DIR
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
        get_highlight_context_from_id,
        expand_found_highlight
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


class SingleHighlightWidget(
        Widget,
        can_focus=True):

    quote = reactive("", layout=True)

    DEFAULT_CSS = """
    SingleHighlightWidget {
        height: auto;
    }
    """

    def __init__(self, option: Option) -> None:
        super().__init__()
        self.book_name = option[0]
        self.highlight = option[1]
        self.highlight_id = option[1].id
        _, _, _, section, book_path = get_highlight_from_database(self.highlight_id)
        self.soup = get_full_context_from_highlight(BOOKS_DIR + book_path,
                                                    section.split('#')[0])
        self.styles.background = "purple"
        # self.styles.width = "60%"
        # self.styles.height = '80%'
        # self.styles.padding = 2

    def render(self) -> Text:
        # start with the minimum possible quote (minimum amount of sentences
        # that enclose the kobo highlight)
        enclosed_highlight = get_highlight_context_from_id(self.highlight_id)
        self.quote = " ".join(enclosed_highlight)
        # get previous and posterior context
        before = " ".join(expand_found_highlight(enclosed_highlight, self.soup, 1, True))
        after = " ".join(expand_found_highlight(enclosed_highlight, self.soup, 1, False))
        text = Text()
        text.append(f"...{before}", style='#828282')
        text.append(f"{self.quote}", style='bold')
        text.append(f"{after}...", style='#828282')
        return text

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


class SingleHighlightsScreen(Screen):

    CSS="""
    #display, #controls {
        width: 1fr;
        margin: 2;
    }
    """

    def __init__(self, name: str, highlight: tuple[str, Option]) -> None:
        super().__init__(name)
        self.highlight=highlight
        self.styles.layout='horizontal'

    def compose(self) -> ComposeResult:
        with VerticalScroll(id = "display"):
            yield SingleHighlightWidget(self.highlight)
        with Vertical(id = "controls"):
            yield TiddlerInformationWidget("TEST", self.highlight)
        yield Header()
        yield Footer()
