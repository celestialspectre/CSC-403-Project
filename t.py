# flask setup instructions: https://flask.palletsprojects.com/en/stable/installation/#install-flask


from flask import *
from database.database import connect_db
#import sqlite3 #later for database integration (if we go with that instead of csv files)
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

@app.route('/character/creator', methods=['GET'])
def character_creator():
    return render_template('characters/creator.html')

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

@app.route("/api/races")
def get_races():
    with connect_db() as conn:
        cursor = conn.execute("""
            SELECT race_id, race_name, description, speed
            FROM races
            ORDER BY race_name
        """)

        races = [{
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "speed": row[3]
        } for row in cursor.fetchall()]

    return jsonify(races)

# <int:race_id> will be passed into get_subraces()
@app.route("/api/races/<int:race_id>/subraces")
def get_subraces(race_id):
    with connect_db() as conn:
        cursor = conn.execute("""
            SELECT subrace_id, subrace_name, description
            FROM subraces
            WHERE race_id = ?
            ORDER BY subrace_name
        """, (race_id,))

        subraces = [{
            "id": row[0],
            "name": row[1],
            "description": row[2]

        } for row in cursor.fetchall()]

    return jsonify(subraces)

@app.route("/api/races/<int:race_id>/bonuses", methods=["GET"])
def get_race_bonuses(race_id):
    with connect_db() as conn:
        cursor = conn.execute("""
            SELECT a.ability_name AS ability, rab.bonus AS bonus, rab.subrace_id AS subrace_id
            FROM race_ability_bonuses AS rab
            JOIN abilities AS a ON rab.ability_id = a.ability_id
            WHERE rab.race_id = ?
        """, (race_id,)).fetchall()

        result = [
            {
                "ability": row[0],
                "bonus": row[1],
                "subrace_id": row[2]
            } for row in cursor
        ]

    return jsonify(result)

@app.route("/api/classes")
def get_classes():
    with connect_db() as conn:
        cursor = conn.execute("""
            SELECT class_id, class_name, description, hit_dice, starting_skills
            FROM classes
            ORDER BY class_name
        """)

        classes = [{
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "hit_dice": row[3],
            "starting_skills": row[4]
        } for row in cursor.fetchall()]

    return jsonify(classes)

@app.route("/api/classes/<int:class_id>/skills", methods=["GET"])
def get_class_skills(class_id):
    with connect_db() as conn:
        cursor = conn.execute("""
            SELECT s.skill_id AS id, s.skill_name AS name, a.ability_name AS ability
            FROM class_skills AS cs
            JOIN skills AS s ON cs.skill_id = s.skill_id
            JOIN abilities AS a ON s.ability_id = a.ability_id
            WHERE cs.class_id = ?
            ORDER BY s.skill_name
        """, (class_id,)).fetchall()

        result = [{
            "id": row[0],
            "name": row[1],
            "ability": row[2]
        } for row in cursor]

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)

