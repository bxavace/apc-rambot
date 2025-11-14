"""API routes and resources for Rambot."""

import threading
import time
from datetime import datetime, timedelta

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    request,
    session as flask_session,
    stream_with_context,
)
from flask_cors import cross_origin
from flask_restful import Api, Resource

from chain import rag_chain, generate_response
from chain_nh import model
from models import db, Conversation, Feedback, Lead, Session
from services.conversation import save_message

api_bp = Blueprint("api", __name__)
api = Api(api_bp)


class GreetTest(Resource):
    @cross_origin()
    def get(self):
        return jsonify(
            {
                "message": (
                    "Everything is absurd. And since everything is absurd, we "
                    "should try to live as happily as possible."
                )
            }
        )


class Chatbot(Resource):
    """Main endpoint of the API (legacy synchronous response)."""

    @cross_origin(supports_credentials=True)
    def post(self):
        session_id = flask_session.get("session_id")
        if not session_id:
            new_session = Session(start_time=datetime.now())
            db.session.add(new_session)
            db.session.commit()
            session_id = new_session.id
            flask_session["session_id"] = session_id

        conversation = flask_session.get(
            "conversation",
            [
                {
                    "role": "ai",
                    "content": (
                        "Welcome to Asia Pacific College! I am Rambot, your 24/7 "
                        "Ram assistant. How can I help you today?"
                    ),
                }
            ],
        )
        data = request.json or {}
        user_message = data.get("user_message")
        time_start = time.time()
        response_payload = rag_chain.invoke({
            "input": user_message,
            "chat_history": conversation,
        })
        response = response_payload["answer"]
        latency = time.time() - time_start

        app = current_app._get_current_object()
        threading.Thread(
            target=save_message,
            args=(app, user_message, response, latency, session_id),
        ).start()

        conversation.extend(
            [
                {"role": "human", "content": user_message},
                {"role": "ai", "content": response},
            ]
        )
        flask_session["conversation"] = conversation

        latest_conversation = Conversation.query.order_by(Conversation.id.desc()).first()
        conversation_id = latest_conversation.id if latest_conversation else None
        return jsonify(
            {
                "response": str(response),
                "responded_in": latency,
                "conversation_id": conversation_id,
                "session_id": session_id,
            }
        )


class ChatbotStream(Resource):
    @cross_origin(supports_credentials=True)
    def post(self):
        data = request.json or {}
        user_message = data.get("message")
        client_session_id = data.get("session_id")

        session_id = _resolve_session(client_session_id)
        current_session = Session.query.filter_by(token=session_id).first()
        if not current_session:
            return jsonify({"message": "Session not found."}), 404

        conversation = _build_conversation_history(current_session, user_message)

        time_start = time.time()
        full_response = ""
        app = current_app._get_current_object()

        def generate():
            nonlocal full_response
            for chunk in generate_response(user_message, conversation):
                full_response += chunk
                yield f"data: {chunk}\n\n"
            yield f"data: {{\"type\": \"session_id\", \"value\": \"{session_id}\"}}\n\n"
            yield "data: [DONE]\n\n"

            latency = time.time() - time_start
            conversation.append({"role": "ai", "content": full_response})
            flask_session["conversation"] = conversation
            flask_session.modified = True

            threading.Thread(
                target=save_message,
                args=(app, user_message, full_response, latency, current_session.id),
            ).start()

        return Response(
            stream_with_context(generate()),
            content_type="text/event-stream",
        )


class FeedbackResource(Resource):
    @cross_origin(supports_credentials=True)
    def put(self):
        data = request.json or {}
        session_id = data.get("session_id")
        is_like = data.get("isLike")
        timestamp = datetime.now()

        current_session = Session.query.filter_by(token=session_id).first()
        if not current_session:
            return jsonify({"message": "Session not found."}), 404

        feedback = Feedback(
            session_id=current_session.id,
            feedback=is_like,
            timestamp=timestamp,
        )
        db.session.add(feedback)
        db.session.commit()

        return jsonify({"message": "Feedback received"})


class ChatbotNoHistory(Resource):
    @cross_origin()
    def post(self):
        data = request.json or {}
        user_message = data.get("user_message")
        time_start = time.time()
        response = model.invoke(user_message)
        latency = time.time() - time_start

        app = current_app._get_current_object()
        threading.Thread(
            target=save_message,
            args=(app, user_message, response, latency, None),
        ).start()

        return jsonify({"response": str(response), "responded_in": latency})


class LeadResource(Resource):
    @cross_origin(supports_credentials=True)
    def post(self):
        data = request.json or {}

        if not data.get("name") or not data.get("email"):
            return jsonify({"message": "Name and email are required."}), 400

        valid_types = ["student", "applicant", "parent", "alumni", "staff", "other"]
        lead_type = data.get("type", "other")
        if lead_type not in valid_types:
            return jsonify({"message": "Invalid lead type."}), 400

        lead = Lead(
            name=data.get("name"),
            email=data.get("email"),
            phone=data.get("phone"),
            type=lead_type,
        )

        db.session.add(lead)
        db.session.commit()

        return jsonify({"message": "Lead added successfully."}), 201

    @cross_origin(supports_credentials=True)
    def get(self, lead_id=None):
        if lead_id:
            lead = Lead.query.get(lead_id)
            if not lead:
                return jsonify({"message": "Lead not found."}), 404

            return jsonify(
                {
                    "id": lead.id,
                    "name": lead.name,
                    "email": lead.email,
                    "phone": lead.phone,
                    "type": lead.type,
                }
            )

        page = request.args.get("page", 1, type=int)
        per_page = 10

        leads = Lead.query.paginate(page=page, per_page=per_page, error_out=False)

        leads_data = [
            {
                "id": lead.id,
                "name": lead.name,
                "email": lead.email,
                "phone": lead.phone,
                "type": lead.type,
            }
            for lead in leads.items
        ]

        return jsonify(
            {
                "leads": leads_data,
                "total_pages": leads.pages,
                "total_items": leads.total,
                "current_page": leads.page,
            }
        )

    @cross_origin(supports_credentials=True)
    def delete(self, lead_id):
        lead = Lead.query.get(lead_id)
        if not lead:
            return jsonify({"message": "Lead not found."}), 404

        db.session.delete(lead)
        db.session.commit()

        return jsonify({"message": "Lead deleted successfully."})


@api_bp.route("/test_session")
@cross_origin(supports_credentials=True)
def test_session():
    flask_session["counter"] = flask_session.get("counter", 0) + 1
    return jsonify({"message": "Counter incremented.", "counter": flask_session["counter"]})


@api_bp.route("/clear_session", methods=["GET"])
@cross_origin(supports_credentials=True)
def clear_session():
    flask_session.clear()
    for key in list(flask_session.keys()):
        flask_session.pop(key, None)
    flask_session.modified = True
    return jsonify({"status": "ok", "message": "Session cleared."}), 200


def _resolve_session(client_session_id):
    if client_session_id:
        session = Session.query.get(client_session_id)
        if session and not session.is_expired:
            session.last_update = datetime.now()
            db.session.commit()
            return client_session_id

    new_session = Session(
        start_time=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=6),
        user_agent=request.user_agent.string,
        ip_address=request.remote_addr,
    )
    db.session.add(new_session)
    db.session.commit()
    flask_session["session_id"] = new_session.token
    return new_session.token


def _build_conversation_history(current_session, user_message):
    previous_conversations = Conversation.query.filter_by(session_id=current_session.id).all()
    conversation = flask_session.get(
        "conversation",
        [
            {
                "role": "ai",
                "content": (
                    "Welcome to Asia Pacific College! I am Rambot, your 24/7 "
                    "Ram assistant. How can I help you today?"
                ),
            }
        ],
    )

    for conv in previous_conversations:
        conversation.append({"role": "human", "content": conv.user_message})
        conversation.append({"role": "ai", "content": conv.bot_response})

    conversation.append({"role": "human", "content": user_message})
    return conversation


api.add_resource(GreetTest, "/api/v1/test")
api.add_resource(FeedbackResource, "/api/feedback")
api.add_resource(LeadResource, "/api/v1/lead", "/api/v1/lead/<int:lead_id>")
api.add_resource(ChatbotStream, "/api/v1/chat-stream")
# Deprecated endpoints left unregistered by default
# api.add_resource(Chatbot, '/api/v1/chat')
# api.add_resource(ChatbotNoHistory, '/api/v1/chat-no-history')
