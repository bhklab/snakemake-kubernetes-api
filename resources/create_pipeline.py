import subprocess
import os
import re
import traceback
from flask_restful import Resource
from flask import request
from db.models.snakemake_pipeline import SnakemakePipeline
from decouple import config
from util.check_token import check_token


class CreatePipeline(Resource):
    method_decorators = [check_token]

    def get(self):
        return "Only post request is allowed", 400

    def post(self):
        status = 200
        response = {}
        pipeline = request.get_json()

        print(pipeline)

        warnings = []
        # check if a snakemake and a dvc repo of the same name already exist.
        snakemake_repo_name = re.findall(r'.*/(.*?).git$', pipeline['git_url'])
        snakemake_repo_name = snakemake_repo_name[0] if len(
            snakemake_repo_name) > 0 else None
        dvc_repo_name = re.findall(r'.*/(.*?).git$', pipeline['dvc_git'])
        dvc_repo_name = dvc_repo_name[0] if len(dvc_repo_name) > 0 else None

        if snakemake_repo_name is None or dvc_repo_name is None:
            warnings.append('Snakemake/DVC repository could not be found.')
        else:
            found = SnakemakePipeline.objects(name=pipeline['name']).first()
            if found is not None:
                warnings.append(
                    'Pipeline {0} already exists.'.format(pipeline['name']))
            # if os.path.isdir(os.path.join(config('SNAKEMAKE_ROOT'), snakemake_repo_name)):
            #     warnings.append(
            #         'Snakemake repository {0} already exists.'.format(snakemake_repo_name))
            if os.path.isdir(os.path.join(config('DVC_ROOT'), dvc_repo_name)):
                warnings.append(
                    'DVC repository {0} already exists.'.format(dvc_repo_name))

        if len(warnings) == 0:
            try:
                # clone the snakemake git repository
                execute_cmd([
                    'git',
                    'clone',
                    pipeline['git_url'],
                    os.path.join(config('SNAKEMAKE_ROOT'),
                                 snakemake_repo_name)
                ])

                # initialize the dvc repository
                execute_cmd([
                    'bash',
                    os.path.join(os.path.abspath(os.getcwd()),
                                 'bash', 'dvc_initialize.sh'),
                    '-w', config('DVC_ROOT'),
                    '-g', pipeline['dvc_git'],
                    '-r', dvc_repo_name,
                    '-d', pipeline['name'],
                    '-f', pipeline['object_name'],
                    '-u', config('S3_URL'),
                    '-i', config('S3_ACCESS_KEY_ID'),
                    '-s', config('S3_SECRET_ACCESS_KEY')
                ])

                # add pipeline document to db
                entry = SnakemakePipeline(**pipeline).save()

                response['message'] = 'Pipeline created'
                response['status'] = 'ok'

            except Exception as e:
                print('Exception ', e)
                print(traceback.format_exc())
                response['error'] = 1
                response['message'] = str(e)
                response['status'] = 'error'
                status = 500
        else:
            response['message'] = 'Pipeline not created'
            response['warnings'] = warnings
            response['status'] = 'error'

        return (response, status)


def execute_cmd(cmd):
    cmd_process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    while True:
        line = cmd_process.stdout.readline()
        if not line:
            break
        else:
            print(line.rstrip().decode("utf-8"))
