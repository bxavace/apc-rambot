from flask import Flask, jsonify, request, Blueprint, render_template, redirect, url_for, Response, session as flask_session, flash
from flask_restful import Api, Resource
from flask_migrate import Migrate
from config import Development, Production
from dotenv import load_dotenv
from chain import rag_chain
from chain_nh import model
from functools import wraps
from langchain_core.messages import HumanMessage, AIMessage
from flask_cors import CORS, cross_origin
from datetime import datetime
from models import db, Conversation, Session, Feedback, Document
from langchain_text_splitters import SpacyTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, WebBaseLoader
from embed import datastore
from markdown import markdown

import os
import threading
import time
import json
import csv
from io import StringIO

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
            new_session = Session(start_time=datetime.now())
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
        return jsonify({'response': str(response), 'responded_in': latency, 'conversation_id': conversation_id, 'session_id': session_id})

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

# markdown template filter
@app.template_filter('markdown')
def convert_markdown(text):
    return markdown(text, extensions=['extra', 'codehilite'])

# Session Testing
@app.route('/test_session')
@cross_origin(supports_credentials=True)
def test_session():
    flask_session['counter'] = flask_session.get('counter', 0) + 1
    return jsonify({'message': 'Counter incremented.', 'counter': flask_session['counter']})

@app.route('/clear_session', methods=['GET'])
@cross_origin(supports_credentials=True)
def clear_session():
    flask_session.clear()
    for key in flask_session.keys():
        flask_session.pop(key, None)
    flask_session.modified = True
    return jsonify({'status': 'ok', 'message': 'Session cleared.'}), 200

###################
### ADMIN PANEL ###
###################
def check_auth(username, password):
    env_username = os.getenv('ADMIN_USERNAME')
    env_password = os.getenv('ADMIN_PASSWORD')
    from hmac import compare_digest
    return compare_digest(username, env_username) and compare_digest(password, env_password)

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
    sessions = Session.query.order_by(Session.start_time.desc()).all()
    return render_template('admin.html', sessions=sessions)

@admin_bp.route('/admin/session/<int:session_id>', methods=['GET'])
@login_required
def view_session(session_id):
    session = Session.query\
        .options(db.joinedload(Session.conversations))\
        .filter_by(id=session_id)\
        .first()
    if session:
        # Sort conversations after fetching since they're already loaded
        conversations = sorted(session.conversations, key=lambda x: x.timestamp)
        print(f"Conversations: {conversations}")
        return render_template('session.html', session=session, conversations=conversations)
    
    flash('Session not found.', 'danger')
    return redirect(url_for('admin.admin'))

@admin_bp.route('/admin/export', methods=['GET'])
@login_required
def export_data():
    return export_csv()

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'md'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'GET':
        return render_template('upload.html')
    
    if 'file' not in request.files:
        flash('No file part', 'warning')
        return redirect(request.url)
    
    files = request.files.getlist('file')
    if not files or all(file.filename == '' for file in files):
        flash('No selected files', 'warning')
        return redirect(request.url)
    
    upload_folder = app.config['UPLOAD_FOLDER']
    responses = []
    
    for file in files:
        if file.filename == '':
            responses.append({'filename': None, 'message': 'No filename provided'})
            continue

        if not allowed_file(file.filename):
            responses.append({'filename': file.filename, 'message': 'Invalid file type'})
            continue

        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > app.config['MAX_FILE_SIZE']:
            responses.append({'filename': file.filename, 'message': 'File too large'})
            continue

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
                responses.append({'filename': new_filename, 'message': 'Upload complete.'})
            else:
                responses.append({'filename': new_filename, 'message': 'Upload failed during processing!'})
        else:
            responses.append({'filename': new_filename, 'message': 'Saving failed.'})
    
    for r in responses:
        flash(f"{r['filename'] or 'Unnamed file'}: {r['message']}", 'info')
    return redirect(url_for('admin.upload'))

@admin_bp.route('/upload-web', methods=['POST'])
@login_required
def upload_web():
    url = request.form.get('url')
    if not url:
        flash('No URL provided.', 'warning')
        return redirect(url_for('admin.upload'))
    
    loader = WebBaseLoader(url)
    data = loader.load()
    if not data:
        flash('No data loaded from URL.', 'warning')
        return redirect(url_for('admin.upload'))
    
    text_splitter = SpacyTextSplitter()
    docs = text_splitter.split_documents(data)
    if not docs:
        flash('No documents were split from the URL.', 'warning')
        return redirect(url_for('admin.upload'))
    
    ids = datastore.add_documents(documents=docs)
    for doc_id in ids:
        document = Document(document_id=doc_id, document_name=url)
        db.session.add(document)
    db.session.commit()
    flash('Upload complete.', 'info')
    return redirect(url_for('admin.upload'))

@admin_bp.route('/documents', methods=['GET'])
@login_required
def get_documents():
    page = request.args.get('page', 1, type=int)  # Get page number from query params
    per_page = 15  # Number of items per page
    documents = Document.query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    return render_template('documents.html', documents=documents)

@admin_bp.route('/documents/<int:id>', methods=['GET'])
@login_required
def get_document(id):
    document = Document.query.get(id)
    if document:
        try:
            with open(document.document_name, 'r', encoding='utf-8') as file:
                content = file.read()
                if document.document_name.lower().endswith('.md'):
                    html_content = markdown(content)
                return render_template('document.html', document=document, content=html_content)
        except Exception as e:
            print(f"Error reading file: {e}")
            document.content = None
            flash(f'Error reading file: {e}', 'danger')
            return redirect(url_for('admin.get_documents'))
    flash('Document not found.', 'danger')
    return redirect(url_for('admin.get_documents'))

@admin_bp.route('/documents/delete/<int:id>', methods=['POST'])
@login_required
def delete_document(id):
    document = Document.query.get(id)
    delete_embeddings(document.document_id)
    # NOTE: the document_name is the filepath
    if os.path.exists(document.document_name):
        os.remove(document.document_name)    
    db.session.delete(document)
    db.session.commit()
    flash('Document deleted successfully.', 'success')
    return redirect(url_for('admin.get_documents'))

def delete_embeddings(document_id):
    try:
        datastore.delete([document_id])
        return True
    except Exception as e:
        print(f"Error deleting document from Azure Search: {e}")
        return False

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
        ids = datastore.add_documents(documents=docs)
        for doc_id in ids:
            document = Document(document_id=doc_id, document_name=filepath)
            db.session.add(document)
        db.session.commit()
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

def export_csv():
    conversations = Conversation.query.all()
    
    # Create a CSV in memory
    csv_output = StringIO()
    csv_writer = csv.writer(csv_output)
    
    # Write header
    csv_writer.writerow(['user_message', 'bot_response', 'timestamp', 'latency'])
    
    # Write data rows
    for conversation in conversations:
        csv_writer.writerow([
            conversation.user_message,
            conversation.bot_response,
            conversation.timestamp,
            conversation.latency
        ])
    
    # Create response
    response = Response(
        csv_output.getvalue(), 
        mimetype='text/csv', 
        headers={'Content-Disposition': 'attachment;filename=conversations.csv'}
    )
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
