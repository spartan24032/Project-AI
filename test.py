from flask import Flask
from flask import render_template
from other import get_data

app = Flask(__name__)

@app.route("/")
def hello_world():
	# Pass these variables to the html file
	return render_template('index.html', data=get_data())