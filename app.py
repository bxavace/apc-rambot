from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Development, Production
from chat import gpt4om
from dotenv import load_dotenv

import os
import threading

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

class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    
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
        data = request.json
        user_message = data.get('user_message')
        response = gpt4om.invoke(user_message)

        threading.Thread(target=save_message, args=(user_message, response.content)).start()

        return jsonify({'response': str(response.content)})

def save_message(user_message, bot_response):
    with app.app_context():
        conversation = Conversation(user_message=user_message, bot_response=bot_response)
        db.session.add(conversation)
        db.session.commit()
        print('Conversation saved.')

with app.app_context():
    db.create_all()

api.add_resource(GreetTest, '/test')
api.add_resource(Chatbot, '/api/v1/chat')

if __name__ == '__main__':
    app.run(debug=True)
