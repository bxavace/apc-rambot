from flask import session as flask_session, request, jsonify, Response
from flask_restful import Resource
from flask_cors import cross_origin

from ..models import Session, Conversation
from ..extensions import db
from ..chain import rag_chain, generate_response
from ..utils import save_message

from datetime import datetime, timedelta

import time
import threading

class Chatbot(Resource):
    @cross_origin()
    def post(self):
        session_id = flask_session.get("session_id")
        if not session_id:
            new_session = Session(start_time=datetime.now())
            db.session.add(new_session)
            db.session.commit()
            session_id = new_session.id
            flask_session["session_id"] = session_id
        
        conversation = flask_session.get("conversation", [
            {
                "role": "ai",
                "content": "Welcome to Asia Pacific College! I am Rambot, your virtual chatbot. How may I help you today?"
            }
        ])
        data = request.json
        user_message = data.get("user_message")
        time_start = time.time()
        response = rag_chain.invoke({
            "input": user_message,
            "chat_history": conversation
        })
        response = response["answer"]
        time_end = time.time()
        latency = time_end - time_start

        threading.Thread(target=save_message, args=(session_id, user_message, "user", latency)).start()

        conversation.extend([
            {"role": "human", "content": user_message},
            {"role": "ai", "content": response}
        ])
        flask_session["conversation"] = conversation

        conversation_id = Conversation.query.order_by(Conversation.id.desc()).first().id
        return jsonify({
            "response": str(response),
            "responded_in": str(latency),
            "conversation_id": str(conversation_id),
            "session_id": str(session_id)
        })

class ChatbotStream(Resource):
    @cross_origin(supports_credentials=True)
    def post(self):
        data = request.json
        user_message = data.get("message")
        client_session_token = data.get("session_id")

        if client_session_token:
            session = Session.query.filter_by(token=client_session_token).first()
            if session and not session.is_expired:
                session_token = client_session_token
                session.last_update = datetime.now()
                db.session.commit()
            else:
                new_session = Session(
                    start_time=datetime.now(),
                    expires_at=datetime.now() + timedelta(hours=3),
                    user_agent=request.user_agent.string,
                    ip_address=request.remote_addr
                )
                db.session.add(new_session)
                db.session.commit()
                session_token = new_session.token
        else:
            new_session = Session(
                start_time=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=3),
                user_agent=request.user_agent.string,
                ip_address=request.remote_addr
            )
            db.session.add(new_session)
            db.session.commit()
            session_token = new_session.token
            flask_session["session_id"] = session_token
        
        session = Session.query.filter_by(token=session_token).first()
        previous_conversations = Conversation.query.filter_by(session_id=session.id).all()

        conversation = flask_session.get("conversation", [
            {
                "role": "ai",
                "content": "Welcome to Asia Pacific College! I am Rambot, your virtual chatbot. How may I help you today?"
            }
        ])

        for conversation in previous_conversations:
            conversation.append({
                "role": "human",
                "content": conversation.user_message
            })
            conversation.append({
                "role": "ai",
                "content": conversation.bot_response
            })
        
        conversation.append({"role": "human", "content": user_message})
        time_start = time.time()
        full_response = ""

        def generate():
            nonlocal full_response
            for chunk in generate_response(user_message, conversation):
                full_response += chunk
                yield f"data: {chunk}\n\n"
            yield f"data: {{\"type\": \"session_token\", \"value\": \"{session_token}\"}}\n\n"
            yield "data [DONE]\n\n"

            time_end = time.time()
            latency = time_end - time_start

            conversation.append({
                "role": "ai",
                "content": full_response
            })
            flask_session["conversation"] = conversation
            flask_session.modified = True

            threading.Thread(target=save_message, args=(session_token, user_message, "user", latency)).start()

        return Response(
            generate(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )