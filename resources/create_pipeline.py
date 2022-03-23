import subprocess, os, threading, re, traceback
import boto3
from flask_restful import Resource
from flask import request

class CreatePipeline(Resource):
    def get(self):
        print('create pipeline')
        status = 200
        response = {}
        
        '''
        Copy the environment variables. The following app-specific environment variables are also imported:
        - GIT_ACCOUNT - GitHub account name where the snakemake repos are hosted.
        - SNAKEMAKE_ROOT - root directory where the Snakefile and env files are stored.
        - DVC_ROOT - root directory where the dvc repositories are stored.
        - S3_BUCKET - bucket name of the S3 storage
        - S3_ACCESS_KEY_ID - access id to ComputeCanada S3 storage.
        - S3_SECRET_ACCESS_KEY - access key to ComputeCanada S3 storage.
        '''
        snakemake_env = os.environ.copy()
        dataname = request.args.get('dataname')
        filename = request.args.get('filename')
        git_url = "https://github.com/" + snakemake_env['GIT_ACCOUNT'] + "/" + dataname + "-snakemake.git" # to be replaced with proper

        repo_name = re.findall(r'.*/(.*?).git$', git_url)
        repo_name = repo_name[0] if len(repo_name) > 0 else None

        if repo_name is not None:
            try:
                # Pull the latest Snakefile and environment configs.
                work_dir = '{0}/{1}'.format(snakemake_env['SNAKEMAKE_ROOT'], repo_name)
                git_process = subprocess.Popen(['git', '-C', work_dir, 'pull'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                git_process.wait()
                
                # Get the commit id of the latest Snakefile version.
                git_process = subprocess.Popen(["git", "ls-remote", git_url], stdout=subprocess.PIPE)
                stdout, std_err = git_process.communicate()
                git_sha = re.split(r'\t+', stdout.decode('ascii'))[0]
            
                # Define the snakemake execution command.
                snakemake_cmd = [
                    'snakemake',
                    '--snakefile', work_dir + '/Snakefile',
                    '--directory', work_dir,
                    '--kubernetes',
                    '--container-image', 'ceeles/snakemake-aks:latest',
                    '--default-remote-prefix', snakemake_env['S3_BUCKET'],
                    '--default-remote-provider', 'S3',
                    '--use-conda',
                    '--jobs', '3',
                    '--config', 
                    'prefix={0}/snakemake/{1}/'.format(snakemake_env['S3_BUCKET'], dataname), 
                    'key={0}'.format(snakemake_env['S3_ACCESS_KEY_ID']), 
                    'secret={0}'.format(snakemake_env['S3_SECRET_ACCESS_KEY']),
                    'host={0}'.format(snakemake_env['S3_URL']),
                    'filename={0}'.format(filename)
                ]
               
                thread = threading.Thread(target=run_in_thread, args=[snakemake_cmd, snakemake_env, dataname, filename])
                thread.start()

                response['message'] = 'Pipeline submitted'
                response['git_url'] = git_url
                response['pipeline_name'] = repo_name
                response['commit_id'] = git_sha
                # TO DO: Insert the data processing entry to db.
            except Exception as e:
                print('Exception ', e)
                print(traceback.format_exc())
                response['error'] = 1
                response['message'] = e
                status = 500
        else:
            response['error'] = 1
            response['message'] = 'Repository name could not be determined. Pipeline not submitted.'

        return(response, status)
    
def run_in_thread(cmd, env, dataname, filename):
    try:
        # Execute the snakemake job.
        snakemake_process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
        s3_client = boto3.client('s3',
                    endpoint_url=env['S3_URL'],
                    aws_access_key_id=env['S3_ACCESS_KEY_ID'],
                    aws_secret_access_key=env['S3_SECRET_ACCESS_KEY']
        )
        s3_client.download_file(
            env['S3_BUCKET'], 
            'snakemake/{0}/{1}'.format(dataname, filename), 
            '{0}/{1}-dvc/{2}'.format(env['DVC_ROOT'], dataname, filename)
        )
        print('download complete')
        
        # Add data to DVC remote.
        cwd = os.path.abspath(os.getcwd())
        add_data_cmd = [
            'bash',
            os.path.join(cwd, 'bash', 'dvc_add.sh'),
            '-r', env['DVC_ROOT'],
            '-d', dataname,
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
        with open(env['DVC_ROOT'] + '/' + dataname + "-dvc/" + filename + ".dvc") as file:
            lines = [line.rstrip() for line in file]
        r = re.compile("^- md5:.*")
        found = next(filter(r.match, lines), None)
        md5 = ""
        if found:
            md5 = re.findall(r'- md5:\s(.*?)$', found)
            print('data added: ' + md5[0])
            # TO DO: update db with the md5 value.
        else:
            print('md5 not found')
    except Exception as e:
        # TO DO: log error to db and email notification.
        print('error')
        raise

