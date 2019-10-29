from app import db
from sqlalchemy.dialects.postgresql import JSON

class Team(db.Model):
  __tablename__ = "teams"

  id = db.Column(db.Integer, primary_key = True)
  team_name = db.Column(db.String(250))

class User(db.Model):
  """docstring for User"""
  __tablename__ = "users"

  id = db.Column(db.Integer(), primary_key = True)
  email = db.Column(db.String(250))
  first_name = db.Column(db.String(250))
  last_name = db.Column(db.String(250))
  team_id = db.Column('team_id',db.Integer, db.ForeignKey('teams.id'), nullable=True)

class Activity(db.Model):
  __tablename__ = "activities"

  id = db.Column(db.Integer, primary_key = True)
  activity_type = db.Column(db.String(10))
  distance = db.Column(db.Float)
  date_completed = db.Column(db.DateTime)
  user_id = db.Column('user_id', db.Integer, db.ForeignKey('users.id'), nullable=False)
