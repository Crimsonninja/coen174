import os
from flask import Flask, escape, request, redirect, render_template, session
from flask_sqlalchemy import SQLAlchemy



app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
from models import Team, User, Activity


@app.route('/')
def hello():
    return "Hello World!"


@app.route('/<name>')
def hello_name(name):
    return "Hello {}!".format(name)

@app.route('/user_main')
def user_main():
    #name = request.args.get("name", "World")
    #return f'Hello, {escape(name)}!'
    # return "Hello World!"
    return render_template('user_index.html')

if __name__ == '__main__':
    app.run()


