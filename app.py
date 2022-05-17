import os, click
from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from db import db
from decouple import config

from resources.create_pipeline import CreatePipeline
from resources.run_pipeline import RunPipeline
from resources.pipeline import ListPipeline
from resources.data_object import ListDataObject, DownloadDataObject
from resources.zenodo import ZenodoUpload
from resources.logs import ListLogs, DownloadLog
from resources.k8 import K8ErrorPods, K8ErrorLog
from resources.test import Test
from maintenance.pipeline import delete

app = Flask(__name__)

# Initialize MongoEngine
app.config['MONGODB_HOST'] = config('MONGODB_HOST')
db.init_app(app)

CORS(app)

# API routes
api = Api(app)
api.add_resource(CreatePipeline, '/api/pipeline/create')
api.add_resource(RunPipeline, '/api/pipeline/run')
api.add_resource(ListPipeline, '/api/pipeline/list')
api.add_resource(ListDataObject, '/api/data_object/list')
api.add_resource(DownloadDataObject, '/api/data_object/download')
api.add_resource(ZenodoUpload, '/api/data_object/upload')
api.add_resource(ListLogs, '/api/log/list')
api.add_resource(DownloadLog, '/api/log/download')
api.add_resource(K8ErrorPods, '/api/k8/error_pods')
api.add_resource(K8ErrorLog, '/api/k8/pod_log')
api.add_resource(Test, '/api/test')

'''
flask cli commands for app/db maintenance
'''
@app.cli.command("delete-pipeline")
@click.option('--pipeline')
def delete_pipeline(pipeline):
    delete(pipeline)