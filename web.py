# flask setup instructions: https://flask.palletsprojects.com/en/stable/installation/#install-flask


from flask import *
import sqlite3   #later for database integration (if we go with that instead of csv files)

app = Flask(__name__) 


# Displays the main character creation page
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


# Gets the information entered into the character form
@app.route("/send_stats", methods=['POST'])
def read_form():

    # Gets each value from the form using its input name
    cName = request.form.get("nameField")
    pName = request.form.get("pNameField")
    cClass = request.form.get("classField")
    cLevel = request.form.get("lvlField")
    cAlign = request.form.get("alignField")
    cRace = request.form.get("raceField")


    # Creates the character stat page using the information from the form
    return f"""
    <head>

        <title>Character Stats</title>

        <link
            rel="stylesheet"
            href="../static/skeleton.css"
        />

    </head>

    <body>

        <div class="statsheet">

            <h1>⚔️ Character Stats ⚔️</h1>

            <h2>Character Name</h2>
            <p name="nameOut" class="inputRes">
                {cName}
            </p>


            <h2>Player</h2>
            <p name="pNameOut" class="inputRes">
                {pName}
            </p>


            <h2>Class</h2>
            <p name="classOut" class="inputRes">
                {cClass}
            </p>


            <h2>Level</h2>
            <p name="lvlOut" class="inputRes">
                {cLevel}
            </p>


            <h2>Alignment</h2>
            <p name="alignOut" class="inputRes">
                {cAlign}
            </p>


            <h2>Race</h2>
            <p name="raceOut" class="inputRes">
                {cRace}
            </p>

        </div>

    </body>
    """, 200

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
                <td>/send_stats</td>
                <td>POST</td>
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


# Starts the Flask application
if __name__ == '__main__':
    app.run(debug=True)

