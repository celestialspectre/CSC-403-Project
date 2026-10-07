# flask setup instructions: https://flask.palletsprojects.com/en/stable/installation/#install-flask

from flask import *
import sqlite3 #later for database integration (if we go with that instead of csv files)

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html') #starts off with the html file placed in the templates folder

@app.route("/send_stats", methods=['POST'])
def read_form():
    #these get whatever was put into the form input fields with corresponding names
    cName = request.form.get("nameField")
    pName = request.form.get("pNameField")
    cClass = request.form.get("classField")
    cLevel = request.form.get("lvlField")
    cAlign = request.form.get("alignField")
    cRace = request.form.get("raceField")


    
    
    #return {"name" : cName}
    # this ugly string is an entire html file with the user inputs subbed in. the return creates a new page with all of their inputs
    return f"<head><title>Stat List</title><link rel=\"stylesheet\" href=\"../static/skeleton.css\" /></head><body><div class=\"statsheet\"><h1>Player Stats</h1><h2>Name</h2><p name=\"nameOut\" class=\"inputRes\">{cName}</p><h2>Player</h2><p name=\"pNameOut\" class=\"inputRes\">{pName}</p><h2>Class</h2><p name=\"classOut\" class=\"inputRes\">{cClass}</p><h2>Level</h2><p name=\"lvlOut\" class=\"inputRes\">{cLevel}</p><h2>Alignment</h2><p name=\"alignOut\" class=\"inputRes\">{cAlign}</p><h2>Race</h2><p name=\"raceOut\" class=\"inputRes\">{cRace}</p></div></body>"



if __name__ == '__main__':
    app.run(debug=True)

