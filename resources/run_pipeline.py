import subprocess
import os
import threading
import re
import traceback
import boto3
import util.run_pipeline_functions.git as git
from flask_restful import Resource
from flask import request
from datetime import datetime
from db.models.snakemake_pipeline import SnakemakePipeline
from db.models.snakemake_data_object import SnakemakeDataObject
from decouple import config
from util.check_token import check_token
from util.run_pipeline_functions.configure_pipeline import configure_pipeline
from util.run_pipeline_functions.find_identical_object import find_identical_object
from util.run_pipeline_functions.get_snakemake_cmd import get_snakemake_cmd
from util.run_pipeline_functions.delete_s3_data import delete_s3_data
from util.run_pipeline_functions.add_to_dvc import add_to_dvc

# S3 storage client used to interact with a remote object storage.
s3_client = boto3.client(
    's3',
    endpoint_url=config('S3_URL'),
    aws_access_key_id=config('S3_ACCESS_KEY_ID'),
    aws_secret_access_key=config('S3_SECRET_ACCESS_KEY')
)

'''
Resource class that triggers a snakemake pipeline run, 
and adds the finalized data object to dvc repo.
'''
class RunPipeline(Resource):
    method_decorators = [check_token]

    def get(self):
        return "Only post request is allowed", 400

    def post(self):
        status = 200
        response = {}

        # Extract req params
        req_body = request.get_json()
        pipeline_name = req_body.get('pipeline')
        run_all = req_body.get('run_all')
        preserved_data = req_body.get('preserved_data')
        preserved_data = [
            'large_data'] + preserved_data if preserved_data is not None and isinstance(preserved_data, list) else []
        request_parameters = req_body.get('additional_parameters')

        pipeline = configure_pipeline(pipeline_name, request_parameters)

        if pipeline is not None:
            try:
                snakemake_repo_name = git.get_repo_name(pipeline.git_url)
                dvc_repo_name = git.get_repo_name(pipeline.dvc_git)
                
                work_dir = os.path.join(config('SNAKEMAKE_ROOT'), snakemake_repo_name)

                git.pull_latest_pipeline(work_dir)

                git_sha = git.get_latest_commit_id(pipeline.git_url)
                
                data_object = find_identical_object(pipeline, git_sha)
                
                if (data_object is None):
                # if (True):
                    for repo in pipeline.additional_repo:
                        repo.commit_id = git.get_latest_commit_id(repo.git_url)

                    snakemake_cmd = get_snakemake_cmd(pipeline, work_dir)
                    print(snakemake_cmd)

                    delete_s3_data(s3_client, pipeline.name, run_all, preserved_data)

                    # Insert the data processing entry to db.
                    entry = SnakemakeDataObject(
                        pipeline=pipeline,
                        additional_repo=pipeline.additional_repo,
                        additional_parameters=pipeline.additional_parameters,
                        commit_id=git_sha,
                        status='processing',
                        process_start_date=datetime.now()
                    ).save()

                    # development code
                    # snakemake_cmd = ''
                    # pipeline_name = 'PSet_GBM'
                    # dvc_repo_name = 'PSet_GBM-dvc'
                    # entry_id = '6427508641c6cf932679f86c'

                    # Start the snakemake job.
                    thread = threading.Thread(
                        target=run_in_thread,
                        args=[
                            snakemake_cmd,
                            pipeline.name,
                            dvc_repo_name,
                            # entry_id
                            str(entry.id)
                        ]
                    )
                    thread.start()

                    response['status'] = 'submitted'
                    response['message'] = 'Pipeline submitted'
                    response['process_id'] = str(entry.id)
                    response['git_url'] = pipeline.git_url
                    response['commit_id'] = git_sha
                else:
                    response['status'] = 'not_submitted'
                    if (data_object.status.value == 'complete') | (data_object.status.value == 'uploaded'):
                        response['message'] = 'A data object processted with the latest %s pipeline already exists.' % pipeline_name
                    if data_object.status.value == 'processing':
                        response['message'] = 'Another data object is currently being processed with %s pipeline.' % pipeline_name
                    response['object'] = data_object.serialize()

            except Exception as e:
                print('Exception ', e)
                print(traceback.format_exc())
                response['error'] = 1
                response['message'] = str(e)
                status = 500
        else:
            response['status'] = 'not_submitted'
            response['message'] = 'Pipeline does not exist.'

        return (response, status)


def run_in_thread(cmd, pipeline_name, dvc_repo_name, object_id):
    try:
        # Execute the snakemake job.
        snakemake_process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            line = snakemake_process.stderr.readline()
            if not line:
                break
            else:
                print(line.rstrip().decode("utf-8"))
        print('execution complete')

        pipeline = SnakemakePipeline.objects(name=pipeline_name).first()
        obj = SnakemakeDataObject.objects(id=object_id).first()
        print(pipeline.object_name)

        if pipeline.object_names is not None:
            print('multiple files')
            
            object_files = list()
            # Add each file to DVC with the same file name due to DVC accepting only one file to be tracked.
            # Record the md5 for each file
            for filename in pipeline.object_names:
                print(filename)
                md5 = add_to_dvc(s3_client, pipeline.name, pipeline.object_name, dvc_repo_name, filename)
                object_files.append({
                    'filename': filename,
                    'md5': md5
                })
            
            obj.update(
                object_files=object_files,
                process_end_date=datetime.now(),
                status='complete'
            )
        else:
            # Add data file to DVC.
            md5 = add_to_dvc(s3_client, pipeline.name, pipeline.object_name, dvc_repo_name)
            if md5:
                obj.update(
                    md5=md5,
                    process_end_date=datetime.now(),
                    status='complete'
                )
            else:
                obj.update(
                    process_end_date=datetime.now(),
                    status='error',
                    error_message=list({'message': 'md5 not found'})
                )
        
        print('complete')
    except Exception as e:
        # TO DO: Log error to db and email notification.
        print('error')
        obj = SnakemakeDataObject.objects(id=object_id).first()
        obj.update(
            process_end_date=datetime.now(),
            status='error',
            error_message=list({'message': str(e)})
        )
        raise
