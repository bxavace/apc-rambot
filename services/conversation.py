"""Conversation-related helpers."""

from models import db, Conversation


def save_message(app, user_message, bot_response, latency, session_id):
    """Persist a conversation exchange inside an application context."""
    with app.app_context():
        conversation = Conversation(
            user_message=user_message,
            bot_response=bot_response,
            latency=latency,
            session_id=session_id,
        )
        db.session.add(conversation)
        db.session.commit()
