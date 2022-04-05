import os
from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from db import db

from resources.run_pipeline import RunPipeline
from resources.test import Test

app = Flask(__name__)

# Initialize MongoEngine
app.config['MONGODB_HOST'] = os.environ.get('MONGODB_HOST')
db.init_app(app)

CORS(app)

# API routes
api = Api(app)
api.add_resource(RunPipeline, '/api/run_pipeline')
api.add_resource(Test, '/api/test')
