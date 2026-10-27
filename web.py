# flask setup instructions: https://flask.palletsprojects.com/en/stable/installation/#install-flask

from flask import *
import sqlite3 #later for database integration (if we go with that instead of csv files)
import hashlib #for hashing the user password

app = Flask(__name__)

# format: @app.route('websitename.xxx/[THIS RIGHT HERE]', methods=['GET'])


# endpoint; url will say '/' when index returns
@app.route('/login', methods=['GET'])

## runs when page opens, starts off with the html file placed in
## the templates folder. For now, this will be the login screen
def index():
    return render_template('login.html') # loads the login.html page


@app.route('/main', methods=['GET'])
def main_menu():
    # get username and password inputted from login page
    username = request.args.get("username", "")
    password = request.args.get("password", "")

    if len(username) < 0:
        return jsonify({"error": "username is required"}), 400
    if len(password) < 0:
        return jsonify({"error": "password is required"}), 400

    return render_template("main.html")

@app.route('/character-creator', methods=['GET'])
def character_creator():
    # username = request.args.get("username", "")
    # password = request.args.get("password", "")

    # if len(username) < 0:
    #     return jsonify({"error": "username is required"}), 400
    # if len(password) < 0:
    #     return jsonify({"error": "password is required"}), 400

    # ===
    # logic for comparing username + password hash to database goes here
    # ===

    # temporary character saving stuff, once database is fully made this can be changed however we need
    with sqlite3.connect('characters.db') as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS characters (id INTEGER PRIMARY KEY, name TEXT, player TEXT, class_name TEXT, level INTEGER, alignment TEXT, race TEXT)')
        characters = conn.execute('SELECT id, name, class_name, level FROM characters ORDER BY id DESC').fetchall()
        

    return """
        <head>
            <title>DND Stat Input</title> <!--name of the tab-->
            <link rel="stylesheet" href="../static/styles/skeleton.css" /> <!--connects the stylesheet (css) to the page-->
        </head>

        <body> 
            <center>
            <form action="/character" method="GET"> <!--sends the form data to the /character endpoint in web.py as a string-->
                <label>Character Name: </label> <!--label for text box-->
                <input required name="nameField"> <!--actual text box-->
                <br /> <!--a line breal to separate elements better-->
                
                <label>Player Name: </label>
                <input required name="pNameField">
                <br />
                
                <label>Class: </label>
                <input required name="classField">
                <br />
                
                <label>Level: </label>
                <input required name="lvlField" type="number" min="1" max="20" step="1">
                <br />
                
                <label>Alignment: </label>
                <input required name="alignField">
                <br />
                
                <label>Race: </label>
                <input required name="raceField">
                <br />

                <label>Check this to go to the json output</label>
                <input type="checkbox" name="sheetCheck">

                <button>Submit</button> <!--submit button-->
                <br />
            </form>
            </center>

            <!--new saved character section of site to list saved characters (what no way)
            <section class="saved-characters">
                <h2>Saved Characters</h2>
                {% if characters %}
                    {% for character in characters %}
                        <p><a href="{{ url_for('saved_character', character_id=character[0]) }}">{{ character[1] }} — {{ character[2] }}, Level {{ character[3] }}</a></p>
                    {% endfor %}
                {% else %}
                    <p>No characters saved yet.</p>
                {% endif %}
            </section>-->
            """,200

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

    pName = request.args.get("pNameField", "")
    cClass = request.args.get("classField", "")
    alignment = request.args.get("alignField", "")
    race = request.args.get("raceField", "")
    
    if request.args.get("sheetCheck"):
        return jsonify({
            "name": name,
            "player": pName,
            "class": cClass,
            "level": int(level),
            "alignment": alignment,
            "race": race,
        }), 200
    return f"""
    <head>
        <title>Stat List</title>
        <link rel=\"stylesheet\" href=\"../static/styles/skeleton.css\" />
    </head>

    <body>
        <div class=\"statsheet\">
            <h1>Player Stats</h1>
            <h2>Name</h2>
            <p name=\"nameOut\" class=\"inputRes\">{name}</p>
            <h2>Player</h2>
            <p name=\"pNameOut\" class=\"inputRes\">{pName}</p>
            <h2>Class</h2>
            <p name=\"classOut\" class=\"inputRes\">{cClass}</p>
            <h2>Level</h2>
            <p name=\"lvlOut\" class=\"inputRes\">{level}</p>
            <h2>Alignment</h2>
            <p name=\"alignOut\" class=\"inputRes\">{alignment}</p>
            <h2>Race</h2>
            <p name=\"raceOut\" class=\"inputRes\">{race}</p>
        </div>
    </body>""", 200


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

