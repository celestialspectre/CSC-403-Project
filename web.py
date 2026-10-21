# flask setup instructions: https://flask.palletsprojects.com/en/stable/installation/#install-flask

from flask import *
import sqlite3 #later for database integration (if we go with that instead of csv files)

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    # temporary character saving stuff, once database is fully made this can be changed however we need
    with sqlite3.connect('characters.db') as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS characters (id INTEGER PRIMARY KEY, name TEXT, player TEXT, class_name TEXT, level INTEGER, alignment TEXT, race TEXT)')
        characters = conn.execute('SELECT id, name, class_name, level FROM characters ORDER BY id DESC').fetchall()
    return render_template('index.html', characters=characters) #starts off with the html file placed in the templates folder

# Endpoint 1
# status check
@app.route('/status', methods=['GET'])
def home():
    return jsonify({"service": "DND Stat Holder", "status": "running"})

# Endpoint 2 
# returns a character as json or 400 on a bad input
@app.route('/character', methods=['GET'])
def character():
    name = request.args.get("nameField", "").strip()
    print("work please!")
    level = request.args.get("lvlField", "")

    if not name:
        return jsonify({"error": "name is required"}), 400

    if not level.isdigit() or not (1 <= int(level) <= 20):
        return jsonify({"error": "level must be a whole number from 1 to 20"}), 400

    pName = request.args.get("pNameField", "")
    cClass = request.args.get("classField", "")
    alignment = request.args.get("alignField", "")
    race = request.args.get("raceField", "")
    
    if request.args.get("sheetCheck"):
        # more temp stuff
        with sqlite3.connect('characters.db') as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS characters (id INTEGER PRIMARY KEY, name TEXT, player TEXT, class_name TEXT, level INTEGER, alignment TEXT, race TEXT)')
            cursor = conn.execute('INSERT INTO characters (name, player, class_name, level, alignment, race) VALUES (?, ?, ?, ?, ?, ?)', (name, pName, cClass, int(level), alignment, race))
            character_id = cursor.lastrowid
        return redirect(url_for('saved_character', character_id=character_id))
        # ^^ temp stuff
        return f"<head><title>Stat List</title><link rel=\"stylesheet\" href=\"../static/skeleton.css\" /></head><body><div class=\"statsheet\"><h1>Player Stats</h1><h2>Name</h2><p name=\"nameOut\" class=\"inputRes\">{name}</p><h2>Player</h2><p name=\"pNameOut\" class=\"inputRes\">{pName}</p><h2>Class</h2><p name=\"classOut\" class=\"inputRes\">{cClass}</p><h2>Level</h2><p name=\"lvlOut\" class=\"inputRes\">{level}</p><h2>Alignment</h2><p name=\"alignOut\" class=\"inputRes\">{alignment}</p><h2>Race</h2><p name=\"raceOut\" class=\"inputRes\">{race}</p></div></body>", 200

    return jsonify({
        "name": name,
        "player": pName,
        "class": cClass,
        "level": int(level),
        "alignment": alignment,
        "race": race,
    }), 200

# selecting a saved character opens its full sheet (again, may be subject to change)
@app.route('/saved/<int:character_id>', methods=['GET'])
def saved_character(character_id):
    with sqlite3.connect('characters.db') as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS characters (id INTEGER PRIMARY KEY, name TEXT, player TEXT, class_name TEXT, level INTEGER, alignment TEXT, race TEXT)')
        row = conn.execute('SELECT name, player, class_name, level, alignment, race FROM characters WHERE id = ?', (character_id,)).fetchone()
    if row is None:
        return jsonify({"error": "character not found"}), 404
    return render_template('sheet.html', character=row)

@app.route("/docs", methods=['GET'])
def docs():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>D&D Stat Holder Documentation</title>
    <head>

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
                <td>status code 200,Character creation page</td>
            </tr>

            <tr>
                <td>/character</td>
                <td>GET</td>
                <td>
                    Character name,<br>
                    player name,<br>
                    class,<br>
                    level,<br>
                    alignment,<br>
                    race
                </td>
                <td>,status code 200,Completed character stat sheet</td>
            </tr>
        </table>
    </body>
    </html>
    """

# @app.route("/send_stats", methods=['POST'])
# def read_form():
#     #these get whatever was put into the form input fields with corresponding names
#     cName = request.form.get("nameField")
#     pName = request.form.get("pNameField")
#     cClass = request.form.get("classField")
#     cLevel = request.form.get("lvlField")
#     cAlign = request.form.get("alignField")
#     cRace = request.form.get("raceField")


    
    
#     #return {"name" : cName}
#     # this ugly string is an entire html file with the user inputs subbed in. the return creates a new page with all of their inputs
#     return f"<head><title>Stat List</title><link rel=\"stylesheet\" href=\"../static/skeleton.css\" /></head><body><div class=\"statsheet\"><h1>Player Stats</h1><h2>Name</h2><p name=\"nameOut\" class=\"inputRes\">{cName}</p><h2>Player</h2><p name=\"pNameOut\" class=\"inputRes\">{pName}</p><h2>Class</h2><p name=\"classOut\" class=\"inputRes\">{cClass}</p><h2>Level</h2><p name=\"lvlOut\" class=\"inputRes\">{cLevel}</p><h2>Alignment</h2><p name=\"alignOut\" class=\"inputRes\">{cAlign}</p><h2>Race</h2><p name=\"raceOut\" class=\"inputRes\">{cRace}</p></div></body>"




if __name__ == '__main__':
    app.run(debug=True)

