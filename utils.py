from datetime import datetime
from flask import current_app

from .extensions import db
from .models import Session, Conversation

def save_message(user_message, bot_response, latency, session_id):
    session = Session.query.filter_by(token=session_id).first()
    if not session:
        current_app.logger.warning(f"Session with token {session_id} not found.")
        return
    
    conversation = Conversation(
        user_message=user_message,
        bot_response=bot_response,
        latency=latency,
        session_id=session.id,
    )
    session.conversations.append(conversation)
    db.session.commit()