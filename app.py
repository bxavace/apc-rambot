from flask import Flask, jsonify, request, Blueprint, render_template, redirect, url_for, Response, session, flash
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Development, Production
from dotenv import load_dotenv
from chain import rag_chain
from functools import wraps
from langchain_core.messages import HumanMessage, AIMessage

import os
import threading
import time
import json

load_dotenv()

app = Flask(__name__)

env = os.getenv('FLASK_ENV', 'development')

if env == 'development':
    app.config.from_object(Development)
else:
    app.config.from_object(Production)

db = SQLAlchemy(app)
api = Api(app)
migrate = Migrate(app, db)
admin_bp = Blueprint('admin', __name__, template_folder='templates')

class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    latency = db.Column(db.Float, default=0.5)

    def __repr__(self):
        return f'<Conversation {self.id}>'

class GreetTest(Resource):
    def get(self):
        return jsonify({'message': 'Everything is absurd. And since everything is absurd, we should try to live as happily as possible.'})

class Chatbot(Resource):
    """
        Main endpoint of the API.
        Update: The saving of the conversation is now done in a separate thread under one resource.
    """
    def post(self):
        conversation = session.get('conversation', [
            {'role': 'ai', 'content': 'Welcome to Asia Pacific College! I am Rambot, your 24/7 Ram assistant. How can I help you today?'}
        ])
        data = request.json
        user_message = data.get('user_message')
        time_start = time.time()
        response = rag_chain.invoke({
            'input': user_message,
            'chat_history': conversation
        })
        response = response['answer']
        time_end = time.time()
        latency = time_end - time_start

        threading.Thread(target=save_message, args=(user_message, response, latency)).start()

        conversation.extend([
            {'role': 'human', 'content': user_message},
            {'role': 'ai', 'content': response}
        ])
        session['conversation'] = conversation

        return jsonify({'response': str(response), 'responded_in': latency})

def save_message(user_message, bot_response, latency):
    with app.app_context():
        conversation = Conversation(user_message=user_message, bot_response=bot_response, latency=latency)
        db.session.add(conversation)
        db.session.commit()
        print('Conversation saved.')

###################
### ADMIN PANEL ###
###################
def check_auth(username, password):
    env_username = os.getenv('ADMIN_USERNAME')
    env_password = os.getenv('ADMIN_PASSWORD')
    return username == env_username and password == env_password

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'authenticated' not in session:
            return redirect(url_for('admin.login', next=url_for('admin.admin')))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    return redirect(url_for('admin.login'))

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check_auth(username, password):
            session['authenticated'] = True
            return redirect(url_for('admin.admin'))
        else:
            flash('Invalid credentials.')
    return render_template('login.html')

@admin_bp.route('/logout')
def logout():
    session.pop('authenticated', None)
    flash('You have been logged out.')
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@login_required
def admin():
    conversations = Conversation.query.order_by(Conversation.timestamp.desc()).all()
    return render_template('admin.html', conversations=conversations)

@admin_bp.route('/admin/export', methods=['GET'])
@login_required
def export_data():
    return export_json()

### CLIENT VIEW TEST ###
@app.route('/client')
def client():
    return render_template('client.html')

@app.route('/<path:path>')
def catch_all(path):
    return render_template('404.html')

def export_json():
    conversations = Conversation.query.all()
    data = []
    for conversation in conversations:
        data.append({
            'user_message': conversation.user_message,
            'bot_response': conversation.bot_response,
            'timestamp': conversation.timestamp,
            'latency': conversation.latency
        })
    json_data = json.dumps(data, default=str)
    response = Response(json_data, mimetype='application/json', headers={'Content-Disposition': 'attachment;filename=conversations.json'})
    return response

app.register_blueprint(admin_bp, url_prefix='/admin')

with app.app_context():
    db.create_all()

api.add_resource(GreetTest, '/api/v1/test')
api.add_resource(Chatbot, '/api/v1/chat')

if __name__ == '__main__':
    app.run(debug=True)
