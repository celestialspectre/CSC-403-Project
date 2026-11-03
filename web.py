import os
import sqlite3
import dice_roll

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    render_template_string,
    flash,
)

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)

from werkzeug.security import generate_password_hash, check_password_hash

from dice_roll import (
    roll_dice,
    d4,
    d6,
    d8,
    d10,
    d12,
    d20,
    d100,
    advantage,
    disadvantage,
    multiple_dice,
    roll_with_modifier
)


app = Flask(__name__)

# Use an environment variable for your secret key in production.
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "change-this-secret-key-for-local-development"
)

# Database file will be created in the same folder as web.py.
DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "characters.db"
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# DATABASE

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character_name TEXT NOT NULL,
                player_name TEXT NOT NULL,
                character_class TEXT NOT NULL,
                character_level INTEGER NOT NULL,
                character_race TEXT NOT NULL,
                character_alignment TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)


initialize_database()


# USER LOGIN

class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = str(user_id)
        self.username = username


@login_manager.user_loader
def load_user(user_id):
    with get_db() as db:
        row = db.execute(
            "SELECT id, username FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

    if row:
        return User(row["id"], row["username"])

    return None


# HTML

STYLE = """
<style>
    * {
        box-sizing: border-box;
    }

    body {
        margin: 0;
        padding: 30px 15px;
        background: #101010;
        color: #f5f5f5;
        font-family: Arial, sans-serif;
    }

    .container {
        max-width: 650px;
        margin: 25px auto;
        padding: 30px;
        background: #1c1c1c;
        border: 1px solid #c9a227;
        border-radius: 12px;
        box-shadow: 0 0 15px rgba(201, 162, 39, 0.12);
    }

    h1, h2 {
        color: #d4af37;
        text-align: center;
    }

    p {
        line-height: 1.5;
    }

    label {
        display: block;
        margin-top: 15px;
        margin-bottom: 6px;
        color: #e4c767;
    }

    input, select {
        width: 100%;
        padding: 11px;
        border-radius: 5px;
        border: 1px solid #555;
        background: #292929;
        color: white;
    }

    button, .button {
        display: inline-block;
        margin-top: 20px;
        padding: 12px 18px;
        border: none;
        border-radius: 5px;
        background: #c9a227;
        color: #111;
        font-weight: bold;
        text-decoration: none;
        cursor: pointer;
    }

    button:hover, .button:hover {
        background: #e4c767;
    }

    .links {
        text-align: center;
        margin-top: 20px;
    }

    .links a, a {
        color: #e4c767;
    }

    .message {
        padding: 10px;
        margin: 12px 0;
        border: 1px solid #c9a227;
        border-radius: 5px;
        color: #f5d778;
    }

    .character {
        padding: 15px;
        margin-top: 15px;
        border: 1px solid #555;
        border-radius: 7px;
        background: #252525;
    }

    .character h3 {
        color: #d4af37;
    }

    .top-links {
        text-align: center;
        margin-bottom: 20px;
    }

    .top-links a {
        margin: 0 8px;
    }
</style>
"""


# LOGIN PAGE

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Welcome to Dungeon & Dragons! - Login</title>
    """ + STYLE + """
</head>
<body>
<div class="container">
    <h1>Welcome to Dungeon & Dragons!</h1>
    <h2>Login</h2>
    <p style="text-align:center;">
        Sign in to create and manage your characters.
    </p>

    {% with messages = get_flashed_messages() %}
      {% for message in messages %}
        <div class="message">{{ message }}</div>
      {% endfor %}
    {% endwith %}

    <form method="POST" action="{{ url_for('login') }}">
        <label for="username">Username</label>
        <input id="username" name="username"
               required autocomplete="username">

        <label for="password">Password</label>
        <input id="password" name="password" type="password"
               required autocomplete="current-password">

        <button type="submit" style="width:100%;">Login</button>
    </form>

    <div class="links">
        <p>Don't have an account?</p>
        <a href="{{ url_for('register') }}">Create an account</a>
    </div>
</div>
</body>
</html>
"""


@app.route("/")
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("character_creator"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with get_db() as db:
            user_row = db.execute(
                """
                SELECT id, username, password_hash
                FROM users
                WHERE username = ?
                """,
                (username,)
            ).fetchone()

        if user_row and check_password_hash(
            user_row["password_hash"], password
        ):
            user = User(user_row["id"], user_row["username"])
            login_user(user)
            return redirect(url_for("character_creator"))

        flash("Invalid username or password.")

    return render_template_string(LOGIN_HTML)


# REGISTRATION

REGISTER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Character Forge - Register</title>
    """ + STYLE + """
</head>
<body>
<div class="container">
    <h1>Character Forge</h1>
    <h2>Create Account</h2>

    {% with messages = get_flashed_messages() %}
      {% for message in messages %}
        <div class="message">{{ message }}</div>
      {% endfor %}
    {% endwith %}

    <form method="POST" action="{{ url_for('register') }}">
        <label for="username">Username</label>
        <input id="username" name="username" required minlength="3"
               maxlength="40" autocomplete="username">

        <label for="password">Password (at least 8 characters)</label>
        <input id="password" name="password" type="password"
               required minlength="8" autocomplete="new-password">

        <button type="submit" style="width:100%;">Register</button>
    </form>

    <div class="links">
        <p>Already have an account?</p>
        <a href="{{ url_for('login') }}">Return to login</a>
    </div>
</div>
</body>
</html>
"""


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("character_creator"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if len(username) < 3 or len(username) > 40:
            flash("Username must be between 3 and 40 characters.")
            return render_template_string(REGISTER_HTML)

        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return render_template_string(REGISTER_HTML)

        password_hash = generate_password_hash(password)

        try:
            with get_db() as db:
                db.execute(
                    """
                    INSERT INTO users (username, password_hash)
                    VALUES (?, ?)
                    """,
                    (username, password_hash)
                )

            flash("Account created successfully. You can now log in.")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("That username is already taken.")

    return render_template_string(REGISTER_HTML)


# LOGOUT

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("login"))


# CHARACTER CREATOR

CREATOR_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Character Forge - Create Character</title>
    """ + STYLE + """
</head>
<body>
<div class="container">
    <h1>Character Forge</h1>

    <div class="top-links">
        Logged in as <strong>{{ current_user.username }}</strong>
        <br>

        <a href="{{ url_for('my_characters') }}">My Characters</a>
        |
        <a href="{{ url_for('dice_roller') }}">Dice Roller</a>
        |
        <a href="{{ url_for('logout') }}">Logout</a>
    </div>

    <h2>Create Your Character</h2>

    {% with messages = get_flashed_messages() %}
      {% for message in messages %}
        <div class="message">{{ message }}</div>
      {% endfor %}
    {% endwith %}

    <form method="POST" action="{{ url_for('send_stats') }}">
        <label for="nameField">Character Name</label>
        <input id="nameField" name="nameField" required maxlength="80">

        <label for="pNameField">Player Name</label>
        <input id="pNameField" name="pNameField" required maxlength="80"
               value="{{ current_user.username }}">

        <label for="classField">Class</label>
        <select id="classField" name="classField" required>
            <option value="">Select a class</option>
            <option>Barbarian</option>
            <option>Bard</option>
            <option>Cleric</option>
            <option>Druid</option>
            <option>Fighter</option>
            <option>Monk</option>
            <option>Paladin</option>
            <option>Ranger</option>
            <option>Rogue</option>
            <option>Sorcerer</option>
            <option>Warlock</option>
            <option>Wizard</option>
        </select>

        <label for="lvlField">Level (1-20)</label>
        <input id="lvlField" name="lvlField" type="number"
               min="1" max="20" value="1" required>

        <label for="raceField">Race</label>
        <select id="raceField" name="raceField" required>
            <option value="">Select a race</option>
            <option>Dragonborn</option>
            <option>Dwarf</option>
            <option>Elf</option>
            <option>Gnome</option>
            <option>Half-Elf</option>
            <option>Half-Orc</option>
            <option>Halfling</option>
            <option>Human</option>
            <option>Tiefling</option>
        </select>

        <label for="alignField">Alignment</label>
        <select id="alignField" name="alignField" required>
            <option value="">Select an alignment</option>
            <option>Lawful Good</option>
            <option>Neutral Good</option>
            <option>Chaotic Good</option>
            <option>Lawful Neutral</option>
            <option>True Neutral</option>
            <option>Chaotic Neutral</option>
            <option>Lawful Evil</option>
            <option>Neutral Evil</option>
            <option>Chaotic Evil</option>
        </select>

        <button type="submit" style="width:100%;">
            Create Character
        </button>
    </form>
</div>
</body>
</html>
"""


@app.route("/character-creator")
@login_required
def character_creator():
    return render_template_string(CREATOR_HTML)


# SAVE AND DISPLAY CHARACTER

CHARACTER_SHEET_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Character Forge - Character Sheet</title>
    """ + STYLE + """
</head>
<body>
<div class="container">
    <h1>Character Forge</h1>
    <h2>Character Sheet</h2>

    <div class="character">
        <h3>{{ character["character_name"] }}</h3>
        <p><strong>Player:</strong> {{ character["player_name"] }}</p>
        <p><strong>Class:</strong> {{ character["character_class"] }}</p>
        <p><strong>Level:</strong> {{ character["character_level"] }}</p>
        <p><strong>Race:</strong> {{ character["character_race"] }}</p>
        <p><strong>Alignment:</strong> {{ character["character_alignment"] }}</p>
    </div>

    <div class="links">
        <a class="button"
           href="{{ url_for('character_creator') }}">Create Another</a>

        <a class="button"
           href="{{ url_for('my_characters') }}">My Characters</a>

        <a class="button"
           href="{{ url_for('dice_roller') }}">Dice Roller</a>

        <a class="button"
           href="{{ url_for('logout') }}">Logout</a>
    </div>
</div>
</body>
</html>
"""


@app.route("/send_stats", methods=["POST"])
@login_required
def send_stats():
    character_name = request.form.get("nameField", "").strip()
    player_name = request.form.get("pNameField", "").strip()
    character_class = request.form.get("classField", "").strip()
    race = request.form.get("raceField", "").strip()
    alignment = request.form.get("alignField", "").strip()

    try:
        level = int(request.form.get("lvlField", "1"))
    except ValueError:
        flash("Level must be a number.")
        return redirect(url_for("character_creator"))

    if not character_name or not player_name:
        flash("Please enter both the character name and player name.")
        return redirect(url_for("character_creator"))

    if not 1 <= level <= 20:
        flash("Character level must be between 1 and 20.")
        return redirect(url_for("character_creator"))

    with get_db() as db:
        cursor = db.execute("""
            INSERT INTO characters (
                user_id, character_name, player_name, character_class,
                character_level, character_race, character_alignment
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            int(current_user.id),
            character_name,
            player_name,
            character_class,
            level,
            race,
            alignment
        ))

        character_id = cursor.lastrowid

        character = db.execute(
            """
            SELECT * FROM characters
            WHERE id = ? AND user_id = ?
            """,
            (character_id, int(current_user.id))
        ).fetchone()

    return render_template_string(
        CHARACTER_SHEET_HTML,
        character=character
    )


# DICE ROLLER HTML

DICE_ROLLER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Character Forge - Dice Roller</title>
    """ + STYLE + """
</head>
<body>
<div class="container">
    <h1>Character Forge</h1>
    <h2>Dice Roller</h2>

    <div class="top-links">
        <a href="{{ url_for('character_creator') }}">Character Creator</a>
        |
        <a href="{{ url_for('my_characters') }}">My Characters</a>
        |
        <a href="{{ url_for('logout') }}">Logout</a>
    </div>

    {% with messages = get_flashed_messages() %}
      {% for message in messages %}
        <div class="message">{{ message }}</div>
      {% endfor %}
    {% endwith %}

    <form method="POST" action="{{ url_for('dice_roller') }}">

        <label for="dice_type">Select Dice Type</label>
        <select id="dice_type" name="dice_type" required>
            <option value="d4">D4</option>
            <option value="d6">D6</option>
            <option value="d8">D8</option>
            <option value="d10">D10</option>
            <option value="d12">D12</option>
            <option value="d20" selected>D20</option>
            <option value="d100">D100</option>
        </select>

        <label for="number">Number of Dice</label>
        <input
            id="number"
            name="number"
            type="number"
            min="1"
            max="100"
            value="1"
            required
        >

        <label for="modifier">Modifier</label>
        <input
            id="modifier"
            name="modifier"
            type="number"
            value="0"
            required
        >

        <label for="roll_type">Roll Type</label>
        <select id="roll_type" name="roll_type" required>
            <option value="normal">Normal Roll</option>
            <option value="advantage">Advantage (D20)</option>
            <option value="disadvantage">Disadvantage (D20)</option>
        </select>

        <button type="submit" style="width:100%;">
            Roll Dice
        </button>
    </form>

    {% if result %}
        <div class="character">
            <h2>Roll Results</h2>

            <p>
                <strong>Dice:</strong>
                {{ result["dice_type"] }}
            </p>

            <p>
                <strong>Individual Rolls:</strong>
                {{ result["rolls"] }}
            </p>

            <p>
                <strong>Modifier:</strong>
                {{ result["modifier"] }}
            </p>

            <h2>Total: {{ result["total"] }}</h2>
        </div>
    {% endif %}

</div>
</body>
</html>
"""


# DICE ROLLER ROUTE

@app.route("/dice-roller", methods=["GET", "POST"])
@login_required
def dice_roller():
    result = None

    if request.method == "POST":

        dice_type = request.form.get("dice_type", "d20")

        try:
            number = int(request.form.get("number", 1))
            modifier = int(request.form.get("modifier", 0))

        except ValueError:
            flash("Please enter valid numbers.")
            return render_template_string(
                DICE_ROLLER_HTML,
                result=None
            )

        roll_type = request.form.get("roll_type", "normal")

        if not 1 <= number <= 100:
            flash("Number of dice must be between 1 and 100.")
            return render_template_string(
                DICE_ROLLER_HTML,
                result=None
            )

        # These shortcuts connect the user's selection
        # to the appropriate dice function in dice_roll.py.

        dice_options = {
            "d4": d4,
            "d6": d6,
            "d8": d8,
            "d10": d10,
            "d12": d12,
            "d20": d20,
            "d100": d100
        }

        if dice_type not in dice_options:
            flash("Invalid dice selection.")
            return render_template_string(
                DICE_ROLLER_HTML,
                result=None
            )

        dice_function = dice_options[dice_type]

        if roll_type == "normal":

            roll_result = roll_with_modifier(
                number,
                dice_function,
                modifier
            )

            rolls = roll_result["rolls"]
            total = roll_result["total"]

        elif roll_type == "advantage":

            if dice_type != "d20" or number != 1:
                flash("Advantage requires one D20.")
                return render_template_string(
                    DICE_ROLLER_HTML,
                    result=None
                )

            roll = advantage()
            rolls = [roll]
            total = roll + modifier

        elif roll_type == "disadvantage":

            if dice_type != "d20" or number != 1:
                flash("Disadvantage requires one D20.")
                return render_template_string(
                    DICE_ROLLER_HTML,
                    result=None
                )

            roll = disadvantage()
            rolls = [roll]
            total = roll + modifier

        else:
            flash("Invalid roll type.")
            return render_template_string(
                DICE_ROLLER_HTML,
                result=None
            )

        result = {
            "dice_type": dice_type.upper(),
            "rolls": rolls,
            "modifier": modifier,
            "total": total
        }

    return render_template_string(
        DICE_ROLLER_HTML,
        result=result
    )


# MY CHARACTERS

MY_CHARACTERS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Character Forge - My Characters</title>
    """ + STYLE + """
</head>
<body>
<div class="container">
    <h1>Character Forge</h1>
    <h2>My Characters</h2>

    <div class="top-links">
        <a href="{{ url_for('character_creator') }}">Create Character</a>
        |
        <a href="{{ url_for('dice_roller') }}">Dice Roller</a>
        |
        <a href="{{ url_for('logout') }}">Logout</a>
    </div>

    {% if characters %}
        {% for character in characters %}
            <div class="character">
                <h3>{{ character["character_name"] }}</h3>
                <p><strong>Player:</strong> {{ character["player_name"] }}</p>
                <p><strong>Class:</strong> {{ character["character_class"] }}</p>
                <p><strong>Level:</strong> {{ character["character_level"] }}</p>
                <p><strong>Race:</strong> {{ character["character_race"] }}</p>
                <p><strong>Alignment:</strong> {{ character["character_alignment"] }}</p>
            </div>
        {% endfor %}
    {% else %}
        <p>You have not created any characters yet.</p>
    {% endif %}
</div>
</body>
</html>
"""


@app.route("/my-characters")
@login_required
def my_characters():
    with get_db() as db:
        characters = db.execute(
            """
            SELECT * FROM characters
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (int(current_user.id),)
        ).fetchall()

    return render_template_string(
        MY_CHARACTERS_HTML,
        characters=characters
    )


# DOCUMENTATION

@app.route("/docs", methods=["GET"])
def docs():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>D&D Stat Holder Documentation</title>
    </head>

    <body>
        <h1>D&D Stat Holder</h1>

        <table border="1">
            <tr>
                <th>Endpoint</th>
                <th>Method</th>
                <th>Expects</th>
                <th>Returns</th>
            </tr>

            <tr>
                <td>/</td>
                <td>GET</td>
                <td>Nothing</td>
                <td>Status code 200, Login page</td>
            </tr>

            <tr>
                <td>/character-creator</td>
                <td>GET</td>
                <td>Logged-in user</td>
                <td>Character creation page</td>
            </tr>

            <tr>
                <td>/send_stats</td>
                <td>POST</td>
                <td>Character information</td>
                <td>Completed character stat sheet</td>
            </tr>

            <tr>
                <td>/my-characters</td>
                <td>GET</td>
                <td>Logged-in user</td>
                <td>Saved characters</td>
            </tr>

            <tr>
                <td>/dice-roller</td>
                <td>GET, POST</td>
                <td>Dice type, number, modifier, roll type</td>
                <td>Dice roll results</td>
            </tr>

            <tr>
                <td>/register</td>
                <td>GET, POST</td>
                <td>Username and password</td>
                <td>Account registration</td>
            </tr>

            <tr>
                <td>/login</td>
                <td>GET, POST</td>
                <td>Username and password</td>
                <td>User login</td>
            </tr>

            <tr>
                <td>/logout</td>
                <td>GET</td>
                <td>Logged-in user</td>
                <td>Logs the user out</td>
            </tr>
        </table>
    </body>
    </html>
    """


# MAIN

if __name__ == "__main__":
    app.run(debug=True)
