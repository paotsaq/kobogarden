import sqlite3
import json
import datetime
import re
import os

SQLITE_DB_PATH = "/home/apinto/"
SQLITE_DB_NAME = "last_kobo_db.sqlite"
EXISTING_IDS_FILE = "/home/apinto/paogarden/existing_ids.txt"

# Connect to the SQLite database
conn = sqlite3.connect(SQLITE_DB_PATH + SQLITE_DB_NAME)
c = conn.cursor()

# Execute the SQL query
c.execute("""
SELECT
Bookmark.BookmarkId,
content.title as BookTitle,
Bookmark.Text,
Bookmark.DateCreated
FROM "Bookmark"
LEFT OUTER JOIN content
ON (content.contentID=Bookmark.VolumeID and content.ContentType=6)
WHERE
Bookmark.Text is not null;
""")

# Fetch all rows from the query
rows = c.fetchall()

# Load existing bookmark ids from file
try:
    with open(EXISTING_IDS_FILE, 'r') as file:
        existing_ids = set(file.read().splitlines())
except FileNotFoundError:
    existing_ids = set()

# Create a list to store tiddlers
tiddlers = []

# Process each row
for row in rows:
    bookmark_id, title, text, date = row

    # Skip this quote if the bookmark id is already in the existing ids set
    if bookmark_id in existing_ids:
        continue

    # Extract the author's name from another table
    c.execute("SELECT Attribution FROM 'content' WHERE Title = ?;", (title,))

    author = c.fetchall()[0][0]

    print(f"found a quote from {title} by {author}\n\n{text}")
    if input("Do you want to keep it? [y]es/[n]o\n") == 'y':
        tiddler_description = input("What should be the tiddler title? ")

        timestamp = datetime.datetime.strptime(date,
                                               '%Y-%m-%dT%H:%M:%S.%f').timestamp()
        # Create a tiddler
        tiddler = {
            "title": f"{tiddler_description}",
            "created": datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d%H%M%S%f')[:-3],
            "creator": 'paotsaq',
            "tags": ['book-quote'],
            "book_title": title,
            "author": author,
            "kobo_bookmark_id": bookmark_id,
            "text": text,
        }
        
        # Save the tiddler
        with open(f"/home/apinto/paogarden/tiddlers/{tiddler_description}.tid", 'w') as file:
            for field in tiddler:
                if field == 'text':
                    continue
                else:
                    file.write(f"{field}: {tiddler[field]}\n")
    # Add the bookmark id to the existing ids set
    existing_ids.add(bookmark_id)

    # Write the tiddler to a separate text file

    with open(EXISTING_IDS_FILE, 'w') as file:
        file.write('\n'.join(existing_ids))

    os.system('clear')
