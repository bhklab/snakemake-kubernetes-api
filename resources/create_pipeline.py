import subprocess, os, threading, re, traceback
from flask_restful import Resource
from flask import request

class CreatePipeline(Resource):
    def get(self):
        print('create pipeline')
        status = 200
        response = {}
        git_url = request.args.get('git_url')
        data_dir = request.args.get('data_dir')

        repo_name = re.findall(r'.*/(.*?).git$', git_url)
        repo_name = repo_name[0] if len(repo_name) > 0 else None

        if repo_name is not None:
            try:
                snakemake_env = os.environ.copy()
                work_dir = '{0}/{1}'.format(snakemake_env['SNAKEMAKE_ROOT'], repo_name)
                
                if os.path.isdir(work_dir):
                    print('git pull')
                    subprocess.Popen(['git', '-C', work_dir, 'pull'], env=snakemake_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                else:
                    print('git clone')
                    subprocess.Popen(['git', 'clone', git_url, work_dir], env=snakemake_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                git_process = subprocess.Popen(["git", "ls-remote", git_url], stdout=subprocess.PIPE)
                stdout, std_err = git_process.communicate()
                git_sha = re.split(r'\t+', stdout.decode('ascii'))[0]
                
                print(work_dir)
                print(snakemake_env['AZ_BLOB_ACCOUNT_URL'])
                print(snakemake_env['AZ_BLOB_CREDENTIAL'])
            
                cmd = [
                    'snakemake',
                    '--snakefile', work_dir + '/Snakefile',
                    '--directory', work_dir,
                    '--kubernetes',
                    '--container-image', 'ceeles/snakemake-aks:latest',
                    '--default-remote-prefix', data_dir,
                    '--default-remote-provider', 'AzBlob',
                    '--envvars', 'AZ_BLOB_ACCOUNT_URL', 'AZ_BLOB_CREDENTIAL',
                    '--use-conda',
                    '--jobs', '3'
                ]

                def run_in_thread():
                    snakemake_process = subprocess.Popen(cmd, env=snakemake_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    out = []
                    while True:
                        line = snakemake_process.stderr.readline()
                        if not line:
                            break
                        else:
                            print(line.rstrip().decode("utf-8"))
                            out.append(line.rstrip().decode("utf-8"))
                    print('execution complete')
                
                thread = threading.Thread(target=run_in_thread)
                thread.start()

                response['message'] = 'Pipeline submitted'
                response['git_url'] = git_url
                response['pipeline_name'] = repo_name
                response['commit_id'] = git_sha
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
