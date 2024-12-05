from textual.binding import Binding

BASE_DIR = '/home/apinto/'
BOOKS_DIR = BASE_DIR + "books/"
PAOGARDEN_DIR = BASE_DIR + "paogarden/"
TIDDLERS_PATH = PAOGARDEN_DIR + "tiddlers/"
IMAGE_FILES_PATH = PAOGARDEN_DIR + "files/"
PROJECT_DIR = BASE_DIR + "kobo_highlights/"
SQLITE_DB_PATH = PROJECT_DIR
SQLITE_DB_NAME = "my_kobo_db.sqlite"
EXISTING_IDS_FILE = "kobo highlight ids of quotes.tid"
DATABASE_PATH = SQLITE_DB_PATH + SQLITE_DB_NAME

CSS_PATH = PROJECT_DIR + "css/"
OPTIONS_CSS_PATH = CSS_PATH + "option_list.tcss"


# Menu VIM bindings
VIM_BINDINGS = [
 Binding("j", "cursor_down", "Down", show=False),
 Binding("shift+g", "last", "Last", show=False),
 Binding("enter", "select", "Select", show=False),
 Binding("gg", "first", "First", show=False),
 Binding("k", "cursor_up", "Up", show=False),
]
