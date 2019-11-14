from app import db
from sqlalchemy.dialects.postgresql import JSON
from flask_security import UserMixin, RoleMixin
from sqlalchemy import BigInteger, func

# CONSTANTS
BIKE_GOAL = 112
RUN_GOAL = 26.2
SWIM_GOAL = 2.4

BIKE_WEIGHT = 0.4
RUN_WEIGHT = 0.3
SWIM_WEIGHT = 0.3

class Team(db.Model):
  __tablename__ = "teams"

  id = db.Column(db.Integer, primary_key = True)
  team_name = db.Column(db.String(250), unique=True)
  member_count = db.Column(db.Integer)
  progress = db.Column(db.Float)
  date_completed = db.Column(db.DateTime)
  status = db.Column(db.String)
  users = db.relationship("User")
  # rank = db.Column(db.Integer)

  def total_team_bike(self):
    users = User.query.filter_by(team_id = self.id).all()
    final_bike = 0
    for user in users:
      final_bike = final_bike + user.total_user_bike()
    return final_bike

  def total_team_run(self):
    users = User.query.filter_by(team_id = self.id).all()
    final_run = 0
    for user in users:
      final_run = final_run + user.total_user_run()
    return final_run

  def total_team_swim(self):
    users = User.query.filter_by(team_id = self.id).all()
    final_swim = 0
    for user in users:
      final_swim = final_swim + user.total_user_swim()
    return final_swim

  # People are welcome to add more distance if they like, but team progress is capped so progress is
  # not increased if more distance is added beyond the goals for each event
  def team_progress(self):
    weighted_swim = self.total_team_swim()/SWIM_GOAL * SWIM_WEIGHT
    if weighted_swim > SWIM_WEIGHT:
      weighted_swim = SWIM_WEIGHT
    print(f'WEIGHTED SWIM: {weighted_swim}')
    weighted_run = self.total_team_run()/RUN_GOAL * RUN_WEIGHT
    if weighted_run > RUN_WEIGHT:
      weighted_run = RUN_WEIGHT
    print(f'WEIGHTED RUN: {weighted_run}')
    weighted_bike = self.total_team_bike()/BIKE_GOAL * BIKE_WEIGHT
    if weighted_bike > BIKE_WEIGHT:
      weighted_bike = BIKE_WEIGHT
    print(f'WEIGHTED BIKE: {weighted_bike}')

    return (weighted_bike + weighted_run + weighted_run)*100

class User(db.Model, UserMixin):
  """docstring for User"""
  __tablename__ = "users"

  id = db.Column(db.Integer, primary_key=True)
  email = db.Column(db.String(250), unique=True)
  first_name = db.Column(db.String(250))
  last_name = db.Column(db.String(250))
  team_id = db.Column('team_id',db.Integer, db.ForeignKey('teams.id'), nullable=True)
  active = db.Column(db.Boolean)
  admin = db.Column(db.Boolean)
  roles = db.relationship('Role', secondary='roles_users', backref=db.backref('users', lazy='dynamic'))
  team = db.relationship("Team", back_populates="users")
  activities = db.relationship("Activity")

  def total_user_bike(self):
    return Activity.query.filter_by(user_id = self.id) \
                .filter_by(status = "approved")  \
                .filter_by(activity_type = "biking") \
                .with_entities(func.sum(Activity.distance)).scalar() or 0

  def total_user_run(self):
    return Activity.query.filter_by(user_id = self.id) \
                .filter_by(status = "approved")  \
                .filter_by(activity_type = "running") \
                .with_entities(func.sum(Activity.distance)).scalar() or 0

  def total_user_swim(self):
    return Activity.query.filter_by(user_id = self.id) \
                .filter_by(status = "approved")  \
                .filter_by(activity_type = "swimming") \
                .with_entities(func.sum(Activity.distance)).scalar() or 0

class Role(db.Model, RoleMixin):
  __tablename__ = 'roles'

  id = db.Column(db.Integer, primary_key = True)
  name = db.Column(db.String(50), unique = True)
  description = db.Column(db.String(255))

class RolesUsers(db.Model):
  __tablename__ = 'roles_users'

  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column('user_id', db.Integer, db.ForeignKey('users.id'))
  role_id = db.Column('role_id', db.Integer, db.ForeignKey('roles.id'))

class Activity(db.Model):
  __tablename__ = "activities"

  id = db.Column(db.Integer, primary_key = True)
  activity_type = db.Column(db.String(10))
  distance = db.Column(db.Float)
  date_completed = db.Column(db.DateTime)
  user_id = db.Column('user_id', db.Integer, db.ForeignKey('users.id'), nullable=False)
  status = db.Column(db.String(30))
  user = db.relationship("User", back_populates="activities")
  status = db.Column(db.String(10))
