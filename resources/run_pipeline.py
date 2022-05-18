import subprocess, os, threading, re, traceback
import boto3
from flask_restful import Resource
from flask import request
from datetime import datetime
from db.models.snakemake_pipeline import SnakemakePipeline
from db.models.snakemake_data_object import SnakemakeDataObject
from decouple import config

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

    def get(self):
        return "Only post request is allowed", 400
    
    def post(self):
        status = 200
        response = {}
        
        snakemake_env = os.environ.copy()
        req_body = request.get_json()
        pipeline_name = req_body.get('pipeline')
        run_all = req_body.get('run_all')
        preserved_data = req_body.get('preserved_data')
        preserved_data = ['large_data'] + preserved_data if preserved_data is not None and isinstance(preserved_data, list) else []

        # find the pipeline
        pipeline = None
        pipeline = SnakemakePipeline.objects(name=pipeline_name).first()

        if pipeline is not None:
            try:
                snakemake_repo_name = re.findall(r'.*/(.*?).git$', pipeline.git_url)
                snakemake_repo_name = snakemake_repo_name[0] if len(snakemake_repo_name) > 0 else None
                dvc_repo_name = re.findall(r'.*/(.*?).git$', pipeline.dvc_git)
                dvc_repo_name = dvc_repo_name[0] if len(dvc_repo_name) > 0 else None
                
                # Pull the latest Snakefile and environment configs.
                work_dir = os.path.join(config('SNAKEMAKE_ROOT'), snakemake_repo_name)
                git_process = subprocess.Popen(['git', '-C', work_dir, 'pull'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                git_process.wait()
                
                # Get the commit id of the latest Snakefile version.
                git_process = subprocess.Popen(["git", "ls-remote", pipeline.git_url], stdout=subprocess.PIPE)
                stdout, std_err = git_process.communicate()
                git_sha = re.split(r'\t+', stdout.decode('ascii'))[0]

                # look for data objects in the db that has been either
                # 1. already processed / uploaded with the latest version of the pipeline, or
                # 2. currently being processed with the requested pipeline.
                data_object = None
                data_object = SnakemakeDataObject.objects(pipeline=pipeline, commit_id=git_sha).first()
                if(data_object is None):
                    data_object = SnakemakeDataObject.objects.filter(pipeline=pipeline, status='processing').first()

                if(data_object is None):
                    for repo in pipeline.additional_data_repo:
                        repo_git_process = subprocess.Popen(["git", "ls-remote", repo.git_url], stdout=subprocess.PIPE)
                        stdout, std_err = repo_git_process.communicate()
                        repo.commit_id = re.split(r'\t+', stdout.decode('ascii'))[0]
                    data_repo = list(map(
                        lambda repo: '{0}={1}'.format(repo.repo_type, repo.git_url.replace('.git', '/raw/{0}/'.format(repo.commit_id))), 
                        pipeline.additional_data_repo
                    ))
                    
                    # Define the snakemake execution command.
                    snakemake_cmd = [
                        '/home/ubuntu/miniconda3/envs/orcestra-snakemake/bin/snakemake',
                        '--snakefile', work_dir + '/Snakefile',
                        '--directory', work_dir,
                        '--kubernetes',
                        '--container-image', config('SNAKEMAKE_DOCKER_IMG'),
                        '--default-remote-prefix', config('S3_BUCKET'),
                        '--default-remote-provider', 'S3',
                        '--jobs', '3',
                        '--config', 
                        'prefix={0}/snakemake/{1}/'.format(config('S3_BUCKET'), pipeline.name), 
                        'key={0}'.format(config('S3_ACCESS_KEY_ID')), 
                        'secret={0}'.format(config('S3_SECRET_ACCESS_KEY')),
                        'host={0}'.format(config('S3_URL')),
                        'filename={0}'.format(pipeline.object_name),
                    ]
                    snakemake_cmd = snakemake_cmd + data_repo

                    # Delete all pipeline data in snakemake object storage if run_all flag is true
                    s3_response = s3_client.list_objects_v2(Bucket=config('S3_BUCKET'), Prefix='snakemake/{0}/'.format(pipeline_name))
                    for obj in s3_response.get('Contents'):
                        key = obj.get('Key')
                        if run_all or not any(map(key.__contains__, preserved_data)):
                            print('Deleting: ' + key)
                            s3_client.delete_object(Bucket=config('S3_BUCKET'), Key=key)

                    # Insert the data processing entry to db.
                    entry = SnakemakeDataObject(
                        pipeline = pipeline,
                        additional_data_repo = pipeline.additional_data_repo,
                        commit_id = git_sha,
                        status = 'processing',
                        process_start_date = datetime.now()
                    ).save()

                    # Start the snakemake job.
                    thread = threading.Thread(
                        target=run_in_thread, 
                        args=[
                            snakemake_cmd, 
                            snakemake_env, 
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

        return(response, status)
    
def run_in_thread(cmd, env, pipeline_name, dvc_repo_name, filename, object_id):
    try:
        # Execute the snakemake job.
        snakemake_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = []
        while True:
            line = snakemake_process.stderr.readline()
            if not line:
                break
            else:
                print(line.rstrip().decode("utf-8"))
                out.append(line.rstrip().decode("utf-8"))
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
        dvc_process = subprocess.Popen(add_data_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
            #Update db with the md5 value.
            obj = SnakemakeDataObject.objects(id = object_id).first()
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
        obj = SnakemakeDataObject.objects(id = object_id).first()
        obj.update(
            process_end_date=datetime.now(),
            status='error',
            error_message=error_message
        )
        raise


