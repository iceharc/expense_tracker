from myapp.models import User
from myapp.__innit__ import db
import myapp.__innit__ as __innit__
new_user = User(
    username="isaac",
    password="hashed_password_here"
)
with __innit__.app_context:
    db.create_all()
db.session.add(new_user)
db.session.commit()
