from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Development, Production

app = Flask(__name__)

if app.env == 'development':
    app.config.from_object(Development)
else:
    app.config.from_object(Production)

db = SQLAlchemy(app)
api = Api(app)
migrate = Migrate(app, db)

class GreetTest(Resource):
    def get(self):
        return jsonify({'message': 'Server operational'})

class Chatbot(Resource):
    """
        Main endpoint of the API.
        This will call '/api/v1/save' to save the user message and bot response.
    """
    def post(self):
        user_message = request.json
        response = ""
        return jsonify({'response': response})

class SaveMessage(Resource):
    """
        Logs the user message and bot response.
    """
    def post(self):
        return jsonify({'message': 'User message saved.'})

with app.app_context():
    db.create_all()

api.add_resource(GreetTest, '/test')
api.add_resource(SaveMessage, '/api/v1/save')
api.add_resource(Chatbot, '/api/v1/chat')

if __name__ == '__main__':
    app.run(debug=True)
