from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
	return "Testing 2 check how to reload...<br> \n Testing one more time..."
