from . import db

class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    latency = db.Column(db.Float, default=0.5)

    def __repr__(self):
        return f'<Conversation {self.id}>'