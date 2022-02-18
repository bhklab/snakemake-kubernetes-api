from flask import Flask
from flask_restful import Api
from flask_cors import CORS

from resources.create_pipeline import CreatePipeline

app = Flask(__name__)
CORS(app)
api = Api(app)

api.add_resource(CreatePipeline, '/api/pipeline/create')
