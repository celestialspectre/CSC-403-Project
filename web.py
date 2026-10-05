# flask setup instructions: https://flask.palletsprojects.com/en/stable/installation/#install-flask
from flask import Flask 

app = Flask(__name__)
output = "<title>DND Stat Tracker</title><h1> Website made!</h1>"

for i in range(0,3):
    output += f"<h1>hi #{i+1}<h1>"

@app.route('/')
def home():
    return output



if __name__ == '__main__':
    app.run(debug=True)

