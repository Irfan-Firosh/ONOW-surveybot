import sqlite3

conn = sqlite3.connect("music.db")
cursor = conn.cursor()

# Create tables
cursor.execute("DROP TABLE IF EXISTS artists")
cursor.execute("DROP TABLE IF EXISTS albums")

cursor.execute("""
CREATE TABLE artists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE albums (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    artist_id INTEGER,
    FOREIGN KEY (artist_id) REFERENCES artists(id)
)
""")

# Insert sample artists
artists = [
    ("Taylor Swift",),
    ("Drake",),
    ("Adele",),
    ("Kanye West",),
    ("Beyoncé",)
]

cursor.executemany("INSERT INTO artists (name) VALUES (?)", artists)

# Insert sample albums
albums = [
    ("1989", 1),
    ("Red", 1),
    ("Certified Lover Boy", 2),
    ("Views", 2),
    ("25", 3),
    ("30", 3),
    ("Donda", 4),
    ("Graduation", 4),
    ("Lemonade", 5)
]

cursor.executemany("INSERT INTO albums (title, artist_id) VALUES (?, ?)", albums)

conn.commit()
conn.close()
