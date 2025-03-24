from . import db
from datetime import datetime, timedelta
import uuid

class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, server_default=db.func.now())
    token = db.Column(db.String(255), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    last_update = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    expires_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now() + timedelta(hours=6))
    user_agent = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(255), nullable=True)
    conversations = db.relationship('Conversation', backref='session', lazy=True)

    @property
    def is_expired(self):
        return datetime.now() > self.expires_at

    def __repr__(self):
        return f'<Session {self.id}>'