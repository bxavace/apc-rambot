from flask import Flask, jsonify
from flask_restful import Api, Resource, reqparse

app = Flask(__name__)
api = Api(app)

class GreetTest(Resource):
    def get(self):
        return jsonify({'message': 'Server operational'})

class SaveMessage(Resource):
    def post(self):
        return jsonify({'message': 'User message saved.'})

api.add_resource(GreetTest, '/test')
api.add_resource(SaveMessage, '/api/v1/save')

if __name__ == '__main__':
    app.run(debug=True)
