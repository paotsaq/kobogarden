from datetime import datetime
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Footer, Header, Input, Button
from textual import events
from textual.message import Message
from textual.screen import Screen
from textual.reactive import reactive
from textual.containers import VerticalScroll, Vertical
from textual.widgets.option_list import Option
from rich.text import Text
from utils.const import (
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
        get_highlight_context_from_id,
        expand_found_highlight
        )


class TiddlerInformationWidget(Widget, can_focus=True):
    edited_quote = reactive("")

    def __init__(self,
                 book_name: str,
                 author: str,
                 highlight_id: int
                 ) -> None:
        super().__init__()
        self.book_name = book_name
        self.author = author
        self.highlight_id = highlight_id

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
        if self.highlight_title.value == "" or self.edited_quote == "":
            return

        # Access or create book tiddler, and retrieve the `highlight_order`
        if book_tiddler_exists(self.book_name):
            highlight_order = increment_book_tiddler_highlight_number(self.book_name)
        else:
            create_book_tiddler(self.book_name, self.author)
            highlight_order = 1

        # Remove the last 3 digits of microseconds
        formatted_now = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]

        # Creates the tiddler string
        tiddler = produce_highlight_tiddler_string(
                formatted_now,
                [self.book_name] + self.highlight_tags.value.split(),
                self.highlight_title.value,
                self.highlight_notes.value,
                self.edited_quote,
                highlight_order
                )

        # Writes the new tiddler file
        with open(TIDDLERS_PATH + self.highlight_title.value + '.tid', "w") as file:
            file.write(tiddler)

        add_highlight_id_to_record(self.highlight_id)


class SingleHighlightWidget(
        Widget,
        can_focus=True):

    quote = reactive("", layout=True)
    fine_before = reactive("", layout=True)
    fine_after = reactive("", layout=True)
    before = reactive("", layout=True)
    after = reactive("", layout=True)
    full_quote = reactive("")

    DEFAULT_CSS = """
    SingleHighlightWidget {
        height: auto;
        padding: 2;
    }
    """

    def __init__(
            self,
            highlight: int,
            soup: str
            ) -> None:
        super().__init__()
        self.highlight = highlight
        self.soup = soup
        self.styles.background = "purple"
        # start with the minimum possible quote
        # (minimum amount of sentences that enclose the kobo highlight)
        # and get previous and posterior context
        self.quote = highlight
        self.before = expand_found_highlight(highlight, self.soup, 2, True)
        self.after = expand_found_highlight(highlight, self.soup, 2, False)

    class SendQuote(Message):
        """Sent when the 'create Tiddler' button is pressed."""

        def __init__(self) -> None:
            super().__init__()

    def watch_full_quote(self) -> None:
        # ask parent Screen to retrieve updated highlight
        self.post_message(self.SendQuote())
        return

    def render(self) -> Text:
        text = Text()
        text.append(f"...{' '.join(self.before)}", style='#828282')
        text.append('|', style='bold blue')
        text.append(f"{self.fine_before}", style='bold')
        text.append(f" {' '.join(self.quote)} " if self.quote else " ", style='bold')
        text.append(f"{self.fine_after}", style='bold')
        text.append('|', style='bold red')
        text.append(f"{' '.join(self.after)}...", style='#828282')
        self.full_quote = " ".join([self.fine_before, " ".join(self.quote), self.fine_after])
        return text

    # TODO these could certainly be refactored
    def contract_quote_above(self, fine=False):
        if fine:
            if self.fine_before != "":
                skip_space = self.fine_before[0] == " " and self.fine_before[1] != " "
                self.before[-1] = self.before[-1] + self.fine_before[:int(skip_space) + 1]
                self.fine_before = self.fine_before[int(skip_space) + 1:]
            # fine_before takes over the first sentence of quote
            else:
                self.before = self.before + [self.quote[0][0]]
                self.fine_before = self.quote[0][1:]
                self.quote = self.quote[1:]
        else:
            if self.fine_before != "":
                self.before[-1] = self.before[-1] + self.fine_before.rstrip()
                self.fine_before = ""
            else:
                if len(self.quote) > 0:
                    self.before = self.before + [self.quote[0]]
                    self.quote = self.quote[1:]

    def extend_quote_above(self, fine=False):
        if fine:
            # receding finely has exhausted the first sentence before
            if self.before[-1] == "":
                self.quote = [self.fine_before.strip()] + self.quote
                self.fine_before = ""
                self.before.pop(-1)
                if len(self.before) == 0:
                    self.before = expand_found_highlight(self.quote, self.soup, 1, True)
            # make cursor skip single spaces
            # NOTE this will crash if there is no before
            skip_space = self.before[-1][-1] == " " and self.before[-1][-2] != " "
            self.fine_before = self.before[-1][-1 - int(skip_space):] + self.fine_before
            self.before = self.before[:-1] + [self.before[-1][:-1 - int(skip_space)]]
        else:
            if self.fine_before != "":
                self.before[-1] = self.before[-1] + self.fine_before.rstrip()
                self.fine_before = ""
            self.quote = [self.before[-1]] + self.quote
            self.before = self.before[:-1]
            if self.before == []:
                self.before = expand_found_highlight(self.quote, self.soup, 1, True)

    def contract_quote_below(self, fine=False):
        if fine:
            if self.fine_after != "":
                self.after[0] = self.fine_after[-1] + self.after[0]
                self.fine_after = self.fine_after[:-1]
            else:
                self.after = [self.quote[-1][-1]] + self.after
                self.fine_after = self.quote[-1][:-1]
                self.quote = self.quote[:-1]
        else:
            if self.fine_after != "":
                self.after[0] = self.fine_after.lstrip() + self.after[0]
                self.fine_after = ""
            else:
                if len(self.quote) > 0:
                    self.after = [self.quote[-1]] + self.after
                    self.quote = self.quote[:-1]

    def extend_quote_below(self, fine=False):
        if fine:
            # advancing finely has exhausted the first sentence after
            if self.after[0] == "":
                self.quote = self.quote + [self.fine_after.strip()]
                self.fine_after = ""
                self.after.pop(0)
                if len(self.after) == 0:
                    self.after = expand_found_highlight(self.quote, self.soup, 1, False)
            # allows for cursor to skip spaces
            # NOTE this will crash if there is no self.after
            skip_space = self.after[0][0] == " " and self.after[0][1] != " "
            self.fine_after = self.fine_after + self.after[0][:int(skip_space) + 1]
            self.after = [self.after[0][1 + int(skip_space):]] + self.after[1:]
        else:
            if self.fine_after != "":
                self.after[0] = self.fine_after.lstrip() + self.after[0]
                self.fine_after = ""
            self.quote = self.quote + [self.after[0]]
            self.after = self.after[1:]
            if self.after == []:
                self.after = expand_found_highlight(
                        self.quote,
                        self.soup, 1, False)


class SingleHighlightsScreen(Screen):
    CSS = """
    #display, #controls {
        width: 1fr;
        margin: 2;
    }
    """

    def __init__(self, name: str, menu_option: tuple[str, Option]) -> None:
        super().__init__(name)
        self.highlight_id = menu_option[1].id
        self.styles.layout = 'horizontal'
        info = get_highlight_from_database(self.highlight_id)
        self.book_name, self.author, _, _, section, path = info
        self.closed_highlight = get_highlight_context_from_id(self.highlight_id)
        self.soup = get_full_context_from_highlight(BOOKS_DIR + path,
                                                    section.split('#')[0])

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="display"):
            yield SingleHighlightWidget(self.closed_highlight,
                                        self.soup)
        with Vertical(id="controls"):
            yield TiddlerInformationWidget(self.book_name,
                                           self.author,
                                           self.highlight_id)
        yield Header()
        yield Footer()

    def on_key(self, event: events.Key) -> None:
        # return to the book highlight screen
        if event.key == "q":
            # TODO this is not working
            self.dismiss(['X', self.highlight_id])
        if event.key == "b":
            self.query_one(SingleHighlightWidget).extend_quote_above()
        if event.key == "B":
            self.query_one(SingleHighlightWidget).contract_quote_above()
        if event.key == "f":
            self.query_one(SingleHighlightWidget).extend_quote_below()
        if event.key == "F":
            self.query_one(SingleHighlightWidget).contract_quote_below()
        if event.key == "j":
            self.query_one(SingleHighlightWidget).extend_quote_above(True)
        if event.key == "J":
            self.query_one(SingleHighlightWidget).contract_quote_above(True)
        if event.key == "k":
            self.query_one(SingleHighlightWidget).extend_quote_below(True)
        if event.key == "K":
            self.query_one(SingleHighlightWidget).contract_quote_below(True)
        if event.key == "t":
            print(self.highlight)

    def on_single_highlight_widget_send_quote(
            self,
            event: SingleHighlightWidget.SendQuote
            ) -> None:
        """"""
        new_highlight = self.query_one(SingleHighlightWidget).full_quote
        self.query_one(TiddlerInformationWidget).edited_quote = new_highlight
