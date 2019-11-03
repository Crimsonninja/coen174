from app import db
from sqlalchemy.dialects.postgresql import JSON
from flask_security import UserMixin, RoleMixin
from sqlalchemy import BigInteger

class Team(db.Model):
  __tablename__ = "teams"

  id = db.Column(db.Integer, primary_key = True)
  team_name = db.Column(db.String(250), unique=True)
  member_count = db.Column(db.Integer)

class User(db.Model, UserMixin):
  """docstring for User"""
  __tablename__ = "users"

  id = db.Column(db.Integer, primary_key=True)
  email = db.Column(db.String(250), unique=True)
  first_name = db.Column(db.String(250))
  last_name = db.Column(db.String(250))
  team_id = db.Column('team_id',db.Integer, db.ForeignKey('teams.id'), nullable=True)
  active = db.Column(db.Boolean)
  roles = db.relationship('Role', secondary='roles_users', backref=db.backref('users', lazy='dynamic'))

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
