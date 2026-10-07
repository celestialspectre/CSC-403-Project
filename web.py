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
    """


# Starts the Flask application
if __name__ == '__main__':
    app.run(debug=True)

