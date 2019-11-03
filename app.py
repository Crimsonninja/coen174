import os, json
from flask import Flask, escape, request, redirect, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import *
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
# from flask_security import Security, SQLAlchemyUserDatastore, \
#    login_required, current_user, login_user, logout_user
from oauthlib.oauth2 import WebApplicationClient
import requests


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Creating database
db = SQLAlchemy(app)

# Google Login Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)



# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Initializing Bootstrap
Bootstrap(app)

# Initializing Navbar
nav = Nav()

# registers the "top" menubar

topbar = Navbar('',
    View('Home', 'index'),
    View('Activities','activities'),
    View('Leaderboard','leaderboard'),
    View('Teams','teams'),
    View('Logout','logout')
    # View('Your Account', 'frontend.account_info'),
)

nav.register_element('top', topbar)

nav.init_app(app)

from models import Team, User, Activity, User, Role

# user_datastore = SQLAlchemyUserDatastore(db.session, User, Role)
# security = Security(app, user_datastore)

# LOGIN Section
@login_manager.user_loader
def load_user(user_id):
  return User.query.get(user_id)

def get_google_provider_cfg():
  return requests.get(GOOGLE_DISCOVERY_URL).json()

@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
  # Get authorization code Google sent back to you
  code = request.args.get("code")

  # Find out what URL to hit to get tokens that allow you to ask for
  # things on behalf of a user
  google_provider_cfg = get_google_provider_cfg()
  token_endpoint = google_provider_cfg["token_endpoint"]

  # Prepare and send a request to get tokens! Yay tokens!
  token_url, headers, body = client.prepare_token_request(
      token_endpoint,
      authorization_response=request.url,
      redirect_url=request.base_url,
      code=code
  )
  token_response = requests.post(
      token_url,
      headers=headers,
      data=body,
      auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
  )

  # Parse the tokens!
  client.parse_request_body_response(json.dumps(token_response.json()))

  # Now that you have tokens (yay) let's find and hit the URL
  # from Google that gives you the user's profile information,
  # including their Google profile image and email
  userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
  uri, headers, body = client.add_token(userinfo_endpoint)
  userinfo_response = requests.get(uri, headers=headers, data=body)

  # You want to make sure their email is verified.
  # The user authenticated with Google, authorized your
  # app, and now you've verified their email through Google!
  if userinfo_response.json().get("email_verified"):
      #unique_id = userinfo_response.json()["sub"]
      users_email = userinfo_response.json()["email"]
      users_first_name = userinfo_response.json()["given_name"]
      users_last_name = userinfo_response.json()["family_name"]
  else:
      return "User email not available or not verified by Google.", 400

  print(f'USERS FIRST NAME IS {users_first_name}!')
  # Create a user in your db with the information provided
  # by Google


  # print(user.first_name)
  # print("The Filter")
  # print(User.query.filter(User.email==user.email))

  # Doesn't exist? Add it to the database.
  if not User.query.filter(User.email==users_email).all():
    user = User(first_name=users_first_name, last_name=users_last_name, email=users_email, active=True)
    db.session.add(user)
    db.session.commit()
    print("COMMITED")
  else:
    user = User.query.filter(User.email==users_email).first()
    #User.create(unique_id, users_name, users_email, picture)

  # Begin user session by logging the user in
  login_user(user)

  # Send user back to homepage
  return redirect(url_for("index"))

@app.route("/logout")
@login_required
def logout():
  logout_user()
  session.clear()
  return redirect(url_for("index"))

@app.route('/')
def index():
  if current_user.is_authenticated:
    return render_template('index.html', user_first_name=current_user.first_name)
  else:
    # return '<a class="button" href="/login">Google Login</a>'
    return render_template('welcome.html')
  # return render_template('index.html', user_first_name=User.query.first().first_name)


@app.route('/<name>')
def hello_name(name):
  return "Hello {}!".format(name)

@app.route('/user_main')
def user_main():
  return render_template('user_index.html')

@app.route('/leaderboard')
def leaderboard():
  return render_template('leaderboard.html')

@app.route('/teams')
def teams():
  valid_team_list = Team.query.filter(Team.member_count < 3).filter(Team.id != current_user.team_id).all()
  return render_template('teams.html', team_exist=False, team_list = valid_team_list)

@app.route('/addteam', methods=['GET','POST'])
def create_team():
    if request.method == 'POST':
        team_name = request.form.get("newteam")
        # If team exists in database
        if Team.query.filter(team_name == Team.team_name).all():
            return render_template('teams.html', team_exist=True)
        else:
            old_team_id = current_user.team_id
            if old_team_id:
                current_user.team_id=None
                if Team.query.get(old_team_id).member_count == 1:
                    db.session.delete(Team.query.get(old_team_id))
                else:
                    old_team = Team.query.get(old_team_id)
                    old_team.member_count = old_team.member_count - 1
            team = Team(team_name=team_name, member_count=1)
            db.session.add(team)
            db.session.commit()
            current_user.team_id = Team.query.filter(team_name == Team.team_name).first().id
            db.session.commit()
            return redirect(url_for("index"))

@app.route('/jointeam/<team_id>', methods=['GET', 'POST'])
def join_team(team_id):
    old_team_id = current_user.team_id
    if old_team_id:
        current_user.team_id=None
        if Team.query.get(old_team_id).member_count == 1:
            Team.query.filter_by(id=old_team_id).delete()
        else:
            old_team = Team.query.get(old_team_id)
            old_team.member_count = old_team.member_count - 1

    team = Team.query.get(team_id)
    team.member_count = team.member_count + 1
    current_user.team_id = team_id
    db.session.commit()
    return redirect(url_for("index"))




@app.route('/activities')
def activities():
  return render_template('activities.html')

if __name__ == '__main__':
  app.run(ssl_context="adhoc")
