from flask import Flask
from flask import render_template
from other import get_data

app = Flask(__name__)

@app.route("/")
def hello_world():
	# Gather data from various sources and assign them to variables
	data_from_other = get_data()
	
    # Pass these variables to the html file
	return render_template('index.html', data=data_from_other)