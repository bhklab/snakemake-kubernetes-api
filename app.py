import os
from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from db import db
from decouple import config

from resources.run_pipeline import RunPipeline
from resources.pipeline import ListPipeline
from resources.data_object import ListDataObject, DownloadDataObject
from resources.zenodo import ZenodoUpload
from resources.logs import ListLogs, DownloadLog
from resources.test import Test

app = Flask(__name__)

# Initialize MongoEngine
app.config['MONGODB_HOST'] = config('MONGODB_HOST')
db.init_app(app)

CORS(app)

# API routes
api = Api(app)
api.add_resource(RunPipeline, '/api/run_pipeline')
api.add_resource(ListPipeline, '/api/pipelines')
api.add_resource(ListDataObject, '/api/data_objects')
api.add_resource(DownloadDataObject, '/api/data_object/download')
api.add_resource(ZenodoUpload, '/api/data_object/upload')
api.add_resource(ListLogs, '/api/logs')
api.add_resource(DownloadLog, '/api/log/download')
api.add_resource(Test, '/api/test')
