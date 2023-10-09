from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Footer, Header, OptionList, Static, Markdown
from textual import events
from textual.screen import Screen
from textual.reactive import reactive
from textual.widgets.option_list import Option, Separator
from utils import (
        get_list_of_highlighted_books,
        get_all_highlights_of_book_from_database,
        get_highlight_from_database,
        get_context_indices_for_highlight_display,
        get_full_context_from_highlight
        )
from rich.table import Table
from rich.text import Text

class SingleHighlightWidget(Widget):
    start = reactive(0)
    end = reactive(0)
    early_context = reactive(0)
    later_context = reactive(0)

    def __init__(self, highlight: Option, soup: str, start: int, end: int) -> None:
        super().__init__()
        self.highlight = highlight
        self.soup = soup
        self.start = start
        self.end = end
        self.early_context = self.start - 300
        self.later_context = self.end + 300

    @staticmethod
    def highlight_generator(highlight: str, date: str) -> Table:
        table = Table(show_header=False)
        table.add_row(date.split('T')[0])
        table.add_row(highlight)
        return table

    def render(self) -> str:
        text = Text()
        text.append(f"...{self.soup[self.early_context:self.start].strip()}", style='#828282')
        text.append(f" {self.soup[self.start:self.end].strip()} ", style='bold')
        text.append(f"{self.soup[self.end:self.later_context].strip()}...", style='#828282')
        return text


class SingleHighlightsScreen(Screen):
    def __init__(self, name: str, highlight: Option) -> None:
        super().__init__(name)
        self.highlight = highlight

    def compose(self) -> ComposeResult:
        _, highlight, _, section, _ = get_highlight_from_database(self.highlight.id)
        soup = get_full_context_from_highlight('./burn.epub', section.split('#')[0])
        start, end = get_context_indices_for_highlight_display(soup, highlight)
        yield SingleHighlightWidget(self.highlight, soup, start, end)
        yield Header()
        yield Footer()

    def on_key(self, event: events.Key) -> None:
        if event.key == "q":
            self.dismiss()
        elif event.key == "h":
            self.query_one(SingleHighlightWidget).start -= 1
        elif event.key == "l":
            self.query_one(SingleHighlightWidget).end -= 1
        elif event.key == "j":
            self.query_one(SingleHighlightWidget).start += 1
        elif event.key == "k":
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

class BookHighlightsWidget(Screen):
    def __init__(self, name: str, selected_option: Option) -> None:
        super().__init__(name)
        self.book = selected_option.id

    @staticmethod
    def highlight_generator(highlight: str, date: str, highlight_id: str) -> Table:
        table = Table(show_header=False)
        table.add_row(date.split('T')[0])
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
            self.dismiss(selected_option)

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
        def check_highlights_panel_quit(highlight: str | None):
            if highlight:
                self.push_screen(SingleHighlightsScreen("panel", highlight))
            else:
                pass

        if event.key == "enter":
            selected_option_index = self.option_list.highlighted
            selected_option = self.option_list._options[selected_option_index]
            self.push_screen(BookHighlightsWidget("panel", selected_option),
                             check_highlights_panel_quit)

if __name__ == "__main__":
    MainScreen().run()
