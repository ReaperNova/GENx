from app.extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class AdminUser(db.Model, UserMixin):
    __tablename__ = "admin_users"

    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(300), nullable=False)
    name          = db.Column(db.String(150), default="Admin")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<AdminUser {self.email}>"


@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))
