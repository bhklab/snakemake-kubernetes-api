from flask import Flask
from flask_restful import Api
from flask_cors import CORS

from resources.run_pipeline import RunPipeline

app = Flask(__name__)
CORS(app)
api = Api(app)

api.add_resource(RunPipeline, '/api/pipeline/run')
