# flask setup instructions: https://flask.palletsprojects.com/en/stable/installation/#install-flask

from flask import *
import sqlite3 #later for database integration (if we go with that instead of csv files)
import hashlib #for hashing the user password

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return render_template('login.html') #starts off with the html file placed in the templates folder. For now, this will be the login screen

@app.route('/login', methods=['GET'])
def login():
    print("hi")
    username = request.args.get("username", "")
    password = request.args.get("password", "")

    if len(username) < 0:
        return jsonify({"error": "username is required"}), 400
    if len(password) < 0:
        return jsonify({"error": "password is required"}), 400

    # ===
    # logic for comparing username + password hash to database goes here
    # ===


    return """
        <head>
            <title>DND Stat Input</title> <!--name of the tab-->
            <link rel="stylesheet" href="../static/styles/skeleton.css" /> <!--connects the stylesheet (css) to the page-->
        </head>


        <body> 
            <center>
            <form action="/character" method="GET"> <!--sends the form data to the /character endpoint in web.py as a string-->
                <label>Name: </label> <!--label for text box-->
                <input name="nameField"> <!--actual text box-->
                <br /> <!--a line breal to separate elements better-->
                
                <label>Player: </label>
                <input name="pNameField">
                <br />
                
                
                <label>Class: </label>
                <input name="classField">
                <br />
                
                <label>Level: </label>
                <input name="lvlField">
                <br />
                
                <label>Alignment: </label>
                <input name="alignField">
                <br />
                
                <label>Race: </label>
                <input name="raceField">
                <br />

                <label>Check this to go to the character sheet</label>
                <input type="checkbox" name="sheetCheck">

                <button>Submit</button> <!--submit button-->
                <br />
            </form>
            </center>
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

    if not name:
        return jsonify({"error": "name is required"}), 400

    if not level.isdigit() or not (1 <= int(level) <= 20):
        return jsonify({"error": "level must be a whole number from 1 to 20"}), 400

    pName = request.args.get("pNameField", "")
    cClass = request.args.get("classField", "")
    alignment = request.args.get("alignField", "")
    race = request.args.get("raceField", "")
    
    if request.args.get("sheetCheck"):
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

    return jsonify({
        "name": name,
        "player": pName,
        "class": cClass,
        "level": int(level),
        "alignment": alignment,
        "race": race,
    }), 200

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

