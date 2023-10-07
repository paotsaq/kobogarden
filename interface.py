from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Footer, Header, OptionList, Placeholder
from textual import events
from textual.screen import Screen
from textual.reactive import reactive
from utils import get_list_of_highlighted_books


class SelectedOptionWidget(Screen):
    def __init__(self, name: str, selected_option: str) -> None:
        super().__init__(name)
        self.selected_option = selected_option

    def on_key(self, event: events.Key) -> None:
        if event.key == "q":
            self.dismiss()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()


class MainScreen(App[None]):
    CSS_PATH = "option_list.tcss"
    COLORS = [
        "white",
        "maroon",
        "red",
        "purple",
        "fuchsia",
        "olive",
        "yellow",
        "navy",
        "teal",
        "aqua",
    ]
    
    def compose(self) -> ComposeResult:
        books = [f'{title} by {author}' for title, author, _
                 in get_list_of_highlighted_books('./test_kobo_db.sqlite')]
        # Store the OptionList instance as an attribute
        self.option_list = OptionList(*books)
        yield Header()
        yield self.option_list  # Yield the stored OptionList instance
        yield Footer()

    def on_mount(self) -> None:
        self.selected_option = None
        self.install_screen(SelectedOptionWidget("panel",
                                                 self.selected_option),
                            name="highlight_panel")

    def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            selected_option_index = self.option_list.highlighted
            self.selected_option = self.option_list._options[selected_option_index]
            self.log(f"You selected: {self.selected_option}")
            self.push_screen("highlight_panel")

if __name__ == "__main__":
    MainScreen().run()
