
# flask setup instructions: https://flask.palletsprojects.com/en/stable/installation/#install-flask

from flask import Flask, render_template, render_template_string, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Connects to the character database
def connect_db():
    conn = sqlite3.connect("characters.db")
    conn.row_factory = sqlite3.Row
    return conn


# Creates the character database if it does not exist
def setup_db():
    conn = connect_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            player TEXT NOT NULL,
            class TEXT NOT NULL,
            level INTEGER NOT NULL,
            alignment TEXT NOT NULL,
            race TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# Allowed character sheet inputs
classes = [
    "Barbarian", "Bard", "Cleric", "Druid", "Fighter",
    "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer",
    "Warlock", "Wizard"
]

alignments = [
    "Lawful Good", "Neutral Good", "Chaotic Good",
    "Lawful Neutral", "True Neutral", "Chaotic Neutral",
    "Lawful Evil", "Neutral Evil", "Chaotic Evil"
]

races = [
    "Human", "Elf", "Dwarf", "Halfling", "Dragonborn",
    "Gnome", "Half-Elf", "Half-Orc", "Tiefling"
]


# Displays the character creation page
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# Displays the character creation menu
@app.route("/menu", methods=["GET"])
def menu():
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>D&D Character Menu</title>
            <link rel="stylesheet" href="/static/skeleton.css">
        </head>
        <body>
            <div class="statsheet">
                <h1>D&D Character Menu</h1>

                <p>
                    <a href="/">Create a New Character</a>
                </p>

                <p>
                    <a href="/characters">View Existing Characters</a>
                </p>
            </div>
        </body>
        </html>
    """)


# Gets the information entered into the character form
@app.route("/send_stats", methods=["POST"])
def read_form():

    # Gets each value from the form using its input name
    cName = request.form.get("nameField", "").strip()
    pName = request.form.get("pNameField", "").strip()
    cClass = request.form.get("classField", "").strip()
    cLevel = request.form.get("lvlField", "").strip()
    cAlign = request.form.get("alignField", "").strip()
    cRace = request.form.get("raceField", "").strip()

    # Checks that all required fields have been entered
    if not all([cName, pName, cClass, cLevel, cAlign, cRace]):
        return "Invalid input: All fields are required.", 400

    # Restricts the length of names
    if len(cName) > 50 or len(pName) > 50:
        return "Invalid input: Names must be 50 characters or less.", 400

    # Checks that the level is a number
    try:
        cLevel = int(cLevel)
    except ValueError:
        return "Invalid input: Level must be a number.", 400

    # Restricts the character level to 1 through 10
    if cLevel < 1 or cLevel > 20:
        return "Invalid input: Level must be between 1 and 20.", 400

    # Checks that the class, alignment, and race are allowed
    if cClass not in classes:
        return "Invalid input: Select a valid class.", 400

    if cAlign not in alignments:
        return "Invalid input: Select a valid alignment.", 400

    if cRace not in races:
        return "Invalid input: Select a valid race.", 400

    # Saves the new character in the database
    conn = connect_db()

    conn.execute("""
        INSERT INTO characters
        (name, player, class, level, alignment, race)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (cName, pName, cClass, cLevel, cAlign, cRace))

    conn.commit()

    # Gets the ID of the new character
    character_id = conn.execute(
        "SELECT last_insert_rowid()"
    ).fetchone()[0]

    conn.close()

    # Opens the saved character sheet
    return redirect(url_for("view_character", character_id=character_id))


# Displays a list of saved characters
@app.route("/characters", methods=["GET"])
def character_list():
    conn = connect_db()

    characters = conn.execute(
        "SELECT id, name, player FROM characters ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Existing Characters</title>
            <link rel="stylesheet" href="/static/skeleton.css">
        </head>
        <body>
            <div class="statsheet">
                <h1>Existing Characters</h1>

                {% if characters %}
                    <ul>
                    {% for character in characters %}
                        <li>
                            <a href="{{ url_for(
                                'view_character',
                                character_id=character['id']
                            ) }}">
                                {{ character['name'] }}
                            </a>
                            - Player: {{ character['player'] }}
                        </li>
                    {% endfor %}
                    </ul>
                {% else %}
                    <p>No characters have been created yet.</p>
                {% endif %}

                <p><a href="/menu">Back to Menu</a></p>
                <p><a href="/">Create a New Character</a></p>
            </div>
        </body>
        </html>
    """, characters=characters)


# Displays the full stats for a selected character
@app.route("/characters/<int:character_id>", methods=["GET"])
def view_character(character_id):
    conn = connect_db()

    character = conn.execute(
        "SELECT * FROM characters WHERE id = ?",
        (character_id,)
    ).fetchone()

    conn.close()

    # Returns an error if the character does not exist
    if character is None:
        return "Character not found.", 404

    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Character Stats</title>
            <link rel="stylesheet" href="/static/skeleton.css">
        </head>
        <body>
            <div class="statsheet">
                <h1>Character Stats</h1>

                <h2>Character Name</h2>
                <p class="inputRes">{{ character['name'] }}</p>

                <h2>Player</h2>
                <p class="inputRes">{{ character['player'] }}</p>

                <h2>Class</h2>
                <p class="inputRes">{{ character['class'] }}</p>

                <h2>Level</h2>
                <p class="inputRes">{{ character['level'] }}</p>

                <h2>Alignment</h2>
                <p class="inputRes">{{ character['alignment'] }}</p>

                <h2>Race</h2>
                <p class="inputRes">{{ character['race'] }}</p>

                <p><a href="/characters">Back to Characters</a></p>
                <p><a href="/menu">Back to Menu</a></p>
            </div>
        </body>
        </html>
    """, character=character)


# Creates the database before the application starts
setup_db()


# Starts the Flask application
if __name__ == "__main__":
    app.run(debug=True)
