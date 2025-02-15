from . import db
from datetime import datetime

class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, server_default=db.func.now())
    conversations = db.relationship('Conversation', backref='session', lazy=True)

    def __repr__(self):
        return f'<Session {self.id}>'