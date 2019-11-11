from app import db
from models import User, Role

# admin_role = Role(name="admin")
# db.session.commit()

user = User.query.get(4)
user.admin = True
db.session.commit()
