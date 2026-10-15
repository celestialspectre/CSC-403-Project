
from flask import Flask, request

app = Flask(__name__)


# Displays the character creation page
@app.route("/")
def index():

    return """
    <!DOCTYPE html>
    <html>

    <head>
        <title>Character Forge</title>

        <style>

            body {
                background: #111111;
                color: white;
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 40px;
            }

            .box {
                background: #1e1e1e;
                border: 2px solid #c9a227;
                border-radius: 15px;
                padding: 35px;
                max-width: 600px;
                margin: auto;
                box-shadow: 0px 0px 30px #000000;
            }

            h1 {
                color: #c9a227;
                font-size: 42px;
            }

            h2 {
                color: #dddddd;
            }

            input, select {
                width: 90%;
                padding: 12px;
                margin: 8px;
                border-radius: 8px;
                border: none;
                font-size: 16px;
                background: #333333;
                color: white;
            }

            button {
                margin-top: 20px;
                padding: 15px 35px;
                border: none;
                border-radius: 10px;
                background: #c9a227;
                color: black;
                font-size: 18px;
                font-weight: bold;
                cursor: pointer;
            }

            button:hover {
                background: #e6c04f;
            }

            .symbol {
                font-size: 50px;
            }

        </style>
    </head>

    <body>

        <div class="box">

            <div class="symbol">⚔️</div>

            <h1>CHARACTER FORGE</h1>

            <h2>Create Your Character</h2>

            <p>Enter your character information below.</p>

            <form action="/send_stats" method="POST">

                <input
                    type="text"
                    name="nameField"
                    placeholder="Character Name"
                >

                <br>

                <input
                    type="text"
                    name="pNameField"
                    placeholder="Player Name"
                >

                <br>

                <select name="classField">

                    <option value="">Choose Class</option>
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

                <br>

                <input
                    type="number"
                    name="lvlField"
                    placeholder="Level"
                    min="1"
                    max="20"
                >

                <br>

                <select name="raceField">

                    <option value="">Choose Race</option>
                    <option>Human</option>
                    <option>Elf</option>
                    <option>Half-Elf</option>
                    <option>Dwarf</option>
                    <option>Halfling</option>
                    <option>Dragonborn</option>
                    <option>Tiefling</option>
                    <option>Half-Orc</option>
                    <option>Gnome</option>

                </select>

                <br>

                <select name="alignField">

                    <option value="">Choose Alignment</option>
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

                <br>

                <button type="submit">
                    ⚔️ CREATE CHARACTER ⚔️
                </button>

            </form>

        </div>

    </body>

    </html>
    """


# Processes the character information from the form
@app.route("/send_stats", methods=["POST"])
def read_form():

    # Gets the information entered by the player
    character_name = request.form.get("nameField")
    player_name = request.form.get("pNameField")
    character_class = request.form.get("classField")
    character_level = request.form.get("lvlField")
    character_race = request.form.get("raceField")
    character_alignment = request.form.get("alignField")

    # Gives default values if a field is left blank
    if not character_name:
        character_name = "Unknown Character"

    if not player_name:
        player_name = "Unknown Player"

    if not character_class:
        character_class = "Adventurer"

    if not character_level:
        character_level = "1"

    if not character_race:
        character_race = "Unknown"

    if not character_alignment:
        character_alignment = "Unaligned"

    # Displays the completed character sheet
    return f"""
    <!DOCTYPE html>

    <html>

    <head>

        <title>{character_name} - Character Sheet</title>

        <style>

            body {{
                background:
                    linear-gradient(
                        135deg,
                        #080808,
                        #191919,
                        #080808
                    );

                color: white;
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 40px;
            }}

            .sheet {{
                max-width: 750px;
                margin: auto;
                background: #171717;
                border: 3px solid #c9a227;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0px 0px 50px #000000;
            }}

            .weapon {{
                font-size: 60px;
            }}

            .title {{
                color: #c9a227;
                font-size: 18px;
                letter-spacing: 6px;
            }}

            h1 {{
                font-size: 48px;
                margin: 10px;
                color: white;
            }}

            .level {{
                display: inline-block;
                background: #c9a227;
                color: black;
                padding: 8px 20px;
                border-radius: 20px;
                font-weight: bold;
            }}

            .stats {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-top: 40px;
            }}

            .stat {{
                background: #222222;
                border: 1px solid #555555;
                border-radius: 12px;
                padding: 25px;
            }}

            .stat-name {{
                color: #999999;
                font-size: 13px;
                letter-spacing: 3px;
            }}

            .stat-value {{
                color: #c9a227;
                font-size: 24px;
                font-weight: bold;
                margin-top: 10px;
            }}

            .divider {{
                margin: 35px;
                color: #c9a227;
                font-size: 25px;
            }}

            a {{
                display: inline-block;
                margin-top: 30px;
                padding: 12px 25px;
                border: 1px solid #c9a227;
                border-radius: 8px;
                color: #c9a227;
                text-decoration: none;
            }}

            a:hover {{
                background: #c9a227;
                color: black;
            }}

        </style>

    </head>

    <body>

        <div class="sheet">

            <div class="weapon">
                ⚔️
            </div>

            <div class="title">
                CHARACTER SHEET
            </div>

            <h1>
                {character_name}
            </h1>

            <div class="level">
                LEVEL {character_level}
            </div>

            <div class="divider">
                ✦ ───────── ✦
            </div>

            <div class="stats">

                <div class="stat">

                    <div class="stat-name">
                        PLAYER
                    </div>

                    <div class="stat-value">
                        {player_name}
                    </div>

                </div>

                <div class="stat">

                    <div class="stat-name">
                        CLASS
                    </div>

                    <div class="stat-value">
                        ⚔️ {character_class}
                    </div>

                </div>

                <div class="stat">

                    <div class="stat-name">
                        RACE
                    </div>

                    <div class="stat-value">
                        🧬 {character_race}
                    </div>

                </div>

                <div class="stat">

                    <div class="stat-name">
                        ALIGNMENT
                    </div>

                    <div class="stat-value">
                        ☯️ {character_alignment}
                    </div>

                </div>

            </div>

            <div class="divider">
                ✦ ───────── ✦
            </div>

            <h2>
                CHARACTER CREATED
            </h2>

            <p>
                Your adventure begins now.
            </p>

            <a href="/">
                ← CREATE ANOTHER CHARACTER
            </a>

        </div>

    </body>

    </html>
    """


# Starts the Flask server
if __name__ == "__main__":
    app.run(debug=True)
