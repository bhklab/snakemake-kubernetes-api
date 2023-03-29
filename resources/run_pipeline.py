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
from db.models.snakemake_data_object import SnakemakeDataObject
from decouple import config
from util.check_token import check_token
from util.run_pipeline_functions.configure_pipeline import configure_pipeline
from util.run_pipeline_functions.find_identical_object import find_identical_object
from util.run_pipeline_functions.get_snakemake_cmd import get_snakemake_cmd
from util.run_pipeline_functions.delete_s3_data import delete_s3_data

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

                    # Start the snakemake job.
                    thread = threading.Thread(
                        target=run_in_thread,
                        args=[
                            snakemake_cmd,
                            pipeline.name,
                            dvc_repo_name,
                            pipeline.object_name,
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


def run_in_thread(cmd, pipeline_name, dvc_repo_name, filename, object_id):
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

        # Download the resulting data from the snakemake job.
        s3_client.download_file(
            config('S3_BUCKET'),
            'snakemake/{0}/{1}'.format(pipeline_name, filename),
            os.path.join(config('DVC_ROOT'), dvc_repo_name, filename)
        )
        print('download complete')

        # Add data to DVC remote.
        cwd = os.path.abspath(os.getcwd())
        add_data_cmd = [
            'bash',
            os.path.join(cwd, 'bash', 'dvc_add.sh'),
            '-r', os.path.join(config('DVC_ROOT'), dvc_repo_name),
            '-d', pipeline_name,
            '-f', filename
        ]
        dvc_process = subprocess.Popen(
            add_data_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            line = dvc_process.stdout.readline()
            if not line:
                break
            else:
                print(line.rstrip().decode("utf-8"))
        with open(os.path.join(config('DVC_ROOT'), dvc_repo_name, filename + ".dvc")) as file:
            lines = [line.rstrip() for line in file]
        r = re.compile("^- md5:.*")
        found = next(filter(r.match, lines), None)
        if found:
            md5 = re.findall(r'- md5:\s(.*?)$', found)
            print('data added: ' + md5[0])
            # Update db with the md5 value.
            obj = SnakemakeDataObject.objects(id=object_id).first()
            obj.update(
                md5=md5[0],
                process_end_date=datetime.now(),
                status='complete'
            )
        else:
            print('md5 not found')

        print('complete')
    except Exception as e:
        # TO DO: Log error to db and email notification.
        print('error')
        obj = SnakemakeDataObject.objects(id=object_id).first()
        obj.update(
            process_end_date=datetime.now(),
            status='error',
            error_message=str(e)
        )
        raise
