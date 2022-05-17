import os, traceback, re, shutil
import boto3
from db.models.snakemake_pipeline import SnakemakePipeline
from db.models.snakemake_data_object import SnakemakeDataObject
from decouple import config

def delete(pipeline):
    warnings = []
    # check if the pipeline exists.
    found = SnakemakePipeline.objects(name=pipeline).first()
    if found is None:
        warnings.append('Pipeline {0} does not exist.'.format(pipeline))
    else:
        snakemake_repo_name = re.findall(r'.*/(.*?).git$', found.git_url)
        snakemake_repo_name = snakemake_repo_name[0]
        dvc_repo_name = re.findall(r'.*/(.*?).git$', found.dvc_git)
        dvc_repo_name = dvc_repo_name[0]
        if not os.path.isdir(os.path.join(config('SNAKEMAKE_ROOT'), snakemake_repo_name)):
            warnings.append('Snakemake repository {0} does not exist.'.format(snakemake_repo_name))
        if not os.path.isdir(os.path.join(config('DVC_ROOT'), dvc_repo_name)):
            warnings.append('DVC repository {0} does not exist.'.format(dvc_repo_name))

    if len(warnings) == 0:
        try:
            # delete snakemake and dvc repo
            shutil.rmtree(os.path.join(config('SNAKEMAKE_ROOT'), snakemake_repo_name))
            shutil.rmtree(os.path.join(config('DVC_ROOT'), dvc_repo_name))

            # delete data object storage
            s3_client = boto3.client(
                's3',
                endpoint_url=config('S3_URL'),
                aws_access_key_id=config('S3_ACCESS_KEY_ID'),
                aws_secret_access_key=config('S3_SECRET_ACCESS_KEY')
            )
            response = s3_client.list_objects_v2(Bucket=config('S3_BUCKET'), Prefix='dvc/{0}/'.format(pipeline))
            for object in response['Contents']:
                s3_client.delete_object(Bucket=config('S3_BUCKET'), Key=object['Key'])
            
            # delete data objects of the pipeline from db
            objects = SnakemakeDataObject.objects.filter(pipeline=found)
            objects.delete()
            
            # delete pipeline from db
            found.delete()

            print('Pipeline deleted')
        except Exception as e:
            print('Exception ', e)
            print(traceback.format_exc())
    else:
        print('Pipeline not deleted')
        for warning in warnings:
            print(warning)

