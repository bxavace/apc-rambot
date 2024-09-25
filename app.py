from flask import Flask, jsonify, request
from flask_restful import Api, Resource, reqparse
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///log.db'

db = SQLAlchemy(app)
api = Api(app)

class GreetTest(Resource):
    def get(self):
        return jsonify({'message': 'Server operational'})

class Chat(Resource):
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

api.add_resource(GreetTest, '/test')
api.add_resource(SaveMessage, '/api/v1/save')
api.add_resource(Chatbot, '/api/v1/chat')

if __name__ == '__main__':
    app.run(debug=True)
