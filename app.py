from flask import Flask, jsonify, request, Blueprint, render_template, redirect, url_for, Response, session as flask_session, flash
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Development, Production
from dotenv import load_dotenv
from chain import rag_chain
from chain_nh import model
from functools import wraps
from langchain_core.messages import HumanMessage, AIMessage
from flask_cors import CORS, cross_origin
from datetime import datetime
from models import db, Conversation, Session, Feedback
from langchain_text_splitters import SpacyTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from embed import datastore

import os
import threading
import time
import json
import hashlib
import glob

load_dotenv()

app = Flask(__name__)

env = os.getenv('FLASK_ENV', 'development')

if env == 'development':
    app.config.from_object(Development)
else:
    app.config.from_object(Production)

db.init_app(app)
api = Api(app)
# TODO: Set the allowed CORS for the admin endpoint
CORS(app, resources={r"/api/*": {"origins": "*"}, r"/client": {"origins": "*"}, r"/test_session": {"origins": "*"}}, supports_credentials=True)
migrate = Migrate(app, db)
admin_bp = Blueprint('admin', __name__, template_folder='templates')

class GreetTest(Resource):
    @cross_origin()
    def get(self):
        return jsonify({'message': 'Everything is absurd. And since everything is absurd, we should try to live as happily as possible.'})

class Chatbot(Resource):
    """
        Main endpoint of the API.
        Update: The saving of the conversation is now done in a separate thread under one resource.
    """
    @cross_origin(supports_credentials=True)
    def post(self):
        session_id = flask_session.get('session_id')
        if not session_id:
            new_session = Session()
            db.session.add(new_session)
            db.session.commit()
            session_id = new_session.id
            flask_session['session_id'] = session_id

        conversation = flask_session.get('conversation', [
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

        threading.Thread(target=save_message, args=(user_message, response, latency, session_id)).start()

        conversation.extend([
            {'role': 'human', 'content': user_message},
            {'role': 'ai', 'content': response}
        ])
        flask_session['conversation'] = conversation

        conversation_id = Conversation.query.order_by(Conversation.id.desc()).first().id
        return jsonify({'response': str(response), 'responded_in': latency, 'conversation_id': conversation_id})

class FeedbackResource(Resource):
    @cross_origin(supports_credentials=True)
    def put(self):
        data = request.json
        session_id = data.get('session_id')
        is_like = data.get('isLike')
        timestamp = datetime.now()
        feedback = Feedback(session_id=session_id, feedback=is_like, timestamp=timestamp)
        db.session.add(feedback)
        db.session.commit()

        return jsonify({'message': 'Feedback received'})

class ChatbotNoHistory(Resource):
    @cross_origin()
    def post(self):
        data = request.json
        user_message = data.get('user_message')
        time_start = time.time()
        response = model.invoke(user_message)
        time_end = time.time()
        latency = time_end - time_start

        threading.Thread(target=save_message, args=(user_message, response, latency)).start()

        return jsonify({'response': str(response), 'responded_in': latency})

def save_message(user_message, bot_response, latency, session_id):
    with app.app_context():
        conversation = Conversation(user_message=user_message, bot_response=bot_response, latency=latency, session_id=session_id)
        db.session.add(conversation)
        db.session.commit()
        print('Conversation saved.')

# Session Testing
@app.route('/test_session')
@cross_origin(supports_credentials=True)
def test_session():
    flask_session['counter'] = flask_session.get('counter', 0) + 1
    return jsonify({'message': 'Counter incremented.', 'counter': flask_session['counter']})

# Session reset
@app.route('/reset_session')
@cross_origin(supports_credentials=True)
def reset_session():
    flask_session.clear()
    flask_session.regenerate()
    return jsonify({'message': 'Session cleared.'})

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
        if 'authenticated' not in flask_session:
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
            flask_session['authenticated'] = True
            return redirect(url_for('admin.admin'))
        else:
            flash('Invalid credentials.')
    return render_template('login.html')

@admin_bp.route('/logout')
def logout():
    flask_session.pop('authenticated', None)
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

@admin_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'GET':
        return render_template('upload.html')
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    upload_folder = app.config['UPLOAD_FOLDER']
    
    base, ext = os.path.splitext(file.filename)
    new_filename = f"{base}{ext}"
    filepath = os.path.join(upload_folder, new_filename)
    
    # If a file with the same name exists, append a timestamp to the filename
    if os.path.exists(filepath):
        timestr = time.strftime("%Y%m%d%H%M%S")
        new_filename = f"{base}_{timestr}{ext}"
        filepath = os.path.join(upload_folder, new_filename)
        
    file.save(filepath)

    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        success = process_file(filepath)
        if success:
            flash('Upload complete.')
            return jsonify({'message': 'ok'})
        else:
            flash('Upload failed during processing!')
            return jsonify({'message': 'failed'})
    else:
        flash('Saving failed.')
        return jsonify({'message': 'failed'})

def process_file(filepath):
    if not os.path.isfile(filepath):
        print(f"Error: File does not exist: {filepath}")
        return False
    if not (filepath.lower().endswith('.pdf') or filepath.lower().endswith('.md')):
        print(f"Error: Invalid file type. Expected a PDF or Markdown: {filepath}")
        return False
    try:
        if filepath.lower().endswith('.pdf'):
            loader = PyPDFLoader(filepath)
            data = loader.load()
        else:  # if markdown file
            loader = TextLoader(filepath, encoding="utf-8")
            data = loader.load()
            
        if not data:
            print(f"Warning: No data loaded from file: {filepath}")
            return False

        text_splitter = SpacyTextSplitter()
        docs = text_splitter.split_documents(data)
        if not docs:
            print(f"Warning: No documents were split from the file: {filepath}")
            return False

        datastore.add_documents(documents=docs)
        return True

    except Exception as e:
        print(f"Error processing file {filepath}: {e}")
        return False

### CLIENT VIEW TEST ###
@app.route('/client')
def client():
    return render_template('client.html')

@app.route('/client-no-history')
def client_no_history():
    return render_template('client_nh.html')

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
api.add_resource(FeedbackResource, '/api/feedback')
api.add_resource(ChatbotNoHistory, '/api/v1/chat-no-history')

if __name__ == '__main__':
    app.run(debug=True)
