import subprocess, os, threading, re, traceback
import boto3
from flask_restful import Resource
from flask import request
from datetime import datetime
from db.models.snakemake_data_object import SnakemakeDataObject
from decouple import config

class RunPipeline(Resource):

    def get(self):
        return "Only post request is allowed", 400
    
    def post(self):
        print('create pipeline')
        status = 200
        response = {}
        
        snakemake_env = os.environ.copy()
        req_body = request.get_json()
        pipeline_name = req_body['pipeline']
        filename = req_body['filename']
        # git_url = 'www.github.com'
        # git_sha = '1234567890'
        # repo_name = 'pdtx-snakemake'

        git_url = "https://github.com/" + config('SNAKEMAKE_GIT_ACCOUNT') + "/" + pipeline_name + "-snakemake.git" # to be replaced with proper

        repo_name = re.findall(r'.*/(.*?).git$', git_url)
        repo_name = repo_name[0] if len(repo_name) > 0 else None

        if repo_name is not None:
            try:
                # Pull the latest Snakefile and environment configs.
                work_dir = '{0}/{1}'.format(config('SNAKEMAKE_ROOT'), repo_name)
                git_process = subprocess.Popen(['git', '-C', work_dir, 'pull'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                git_process.wait()
                
                # Get the commit id of the latest Snakefile version.
                git_process = subprocess.Popen(["git", "ls-remote", git_url], stdout=subprocess.PIPE)
                stdout, std_err = git_process.communicate()
                git_sha = re.split(r'\t+', stdout.decode('ascii'))[0]

                object = SnakemakeDataObject.objects(pipeline_name=pipeline_name, commit_id=git_sha).first()
                if(object is None):
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
                        '-R', 'get_pset',
                        '--config', 
                        'prefix={0}/snakemake/{1}/'.format(config('S3_BUCKET'), pipeline_name), 
                        'key={0}'.format(config('S3_ACCESS_KEY_ID')), 
                        'secret={0}'.format(config('S3_SECRET_ACCESS_KEY')),
                        'host={0}'.format(config('S3_URL')),
                        'filename={0}'.format(filename)
                    ]

                    # Insert the data processing entry to db.
                    entry = SnakemakeDataObject(
                        pipeline_name = pipeline_name,
                        filename = filename,
                        git_url = git_url,
                        commit_id = git_sha,
                        status = 'processing',
                        process_start_date = datetime.now()
                    ).save()

                    # Start the snakemake job.
                    thread = threading.Thread(target=run_in_thread, args=[snakemake_cmd, snakemake_env, pipeline_name, filename, str(entry.id)])
                    thread.start()

                    response['message'] = 'Pipeline submitted'
                    response['process_id'] = str(entry.id)
                    response['git_url'] = git_url
                    response['repository_name'] = repo_name
                    response['commit_id'] = git_sha
                else:
                    response['message'] = 'A %s data object with the latest pipeline already exists' % pipeline_name
                    response['object'] = object.serialize()
            except Exception as e:
                print('Exception ', e)
                print(traceback.format_exc())
                response['error'] = 1
                response['message'] = str(e)
                status = 500
        else:
            response['error'] = 1
            response['message'] = 'Repository name could not be found. Pipeline not submitted.'

        return(response, status)
    
def run_in_thread(cmd, env, pipeline_name, filename, object_id):
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
        s3_client = boto3.client(
            's3',
            endpoint_url=config('S3_URL'),
            aws_access_key_id=config('S3_ACCESS_KEY_ID'),
            aws_secret_access_key=config('S3_SECRET_ACCESS_KEY')
        )
        s3_client.download_file(
            config('S3_BUCKET'), 
            'snakemake/{0}/{1}'.format(pipeline_name, filename), 
            '{0}/{1}-dvc/{2}'.format(config('DVC_ROOT'), pipeline_name, filename)
        )
        print('download complete')
        
        # Add data to DVC remote.
        cwd = os.path.abspath(os.getcwd())
        add_data_cmd = [
            'bash',
            os.path.join(cwd, 'bash', 'dvc_add.sh'),
            '-r', config('DVC_ROOT'),
            '-d', pipeline_name,
            '-f', filename
        ]
        dvc_process = subprocess.Popen(add_data_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        dvc_p_out = []
        while True:
            line = dvc_process.stdout.readline()
            if not line:
                break
            else:
                print(line.rstrip().decode("utf-8"))
                dvc_p_out.append(line.rstrip().decode("utf-8"))
        with open(config('DVC_ROOT') + '/' + pipeline_name + "-dvc/" + filename + ".dvc") as file:
            lines = [line.rstrip() for line in file]
        r = re.compile("^- md5:.*")
        found = next(filter(r.match, lines), None)
        md5 = ""
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
    except Exception as e:
        #Log error to db and email notification.
        print('error')
        update_db_with_error(object_id, str(e))
        raise

def update_db_with_error(object_id, error_message):
    obj = SnakemakeDataObject.objects(id = object_id).first()
    obj.update(
        process_end_date=datetime.now(),
        status='error',
        error_message=error_message
    )
