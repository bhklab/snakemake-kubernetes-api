import os, traceback, boto3
from flask_restful import Resource
from flask import request, send_file
from db.models.snakemake_data_object import SnakemakeDataObject

class ListDataObject(Resource):
    '''
    API route: /api/data_objects
    Accepted query parameters:
        status (optional, defaults to 'complete'): processing, complete or uploaded
        pipeline_name (optional): string value for pipeline name
        latest (optional, defaults to 'false'): boolean, if true, returns the latest pipeline run filtered with other parameters.
    '''
    def get(self):
        status = 200
        response = {}
        try:
            query = {
                'status': 'complete'
            }
            status = request.args.get('status')
            pipeline_name = request.args.get('pipeline_name')
            latest = request.args.get('latest')
            if status is not None and status != 'complete':
                query['status'] = status
            if pipeline_name is not None:
                query['pipeline_name'] = pipeline_name
            
            objects = SnakemakeDataObject.objects(**query).order_by('-id')
            
            if latest:
                response['object'] = objects[0].serialize()
            else:
                response['objects'] = SnakemakeDataObject.serialize_list(objects)
        except Exception as e:
            print('Exception ', e)
            print(traceback.format_exc())
            response['error'] = 1
            response['message'] = e
            status = 500
        finally:
            return response, status
    
    def post(self):
        return 'Only get request is allowed', 400

class DownloadDataObject(Resource):
    def get(self):
        status = 200
        response = {}
        env = os.environ
        object = None
        file_path = None
        try:
            data_obj_id = request.args.get('data_obj_id')
            if(data_obj_id is not None):
                object = SnakemakeDataObject.objects(pk=data_obj_id).first()

            if(object is not None):
                if object.status.value == 'processing':
                    response['message'] = 'Unable to download. Data object is being processed.'
                else:
                    tmp_dir = '{0}/{1}'.format(os.environ ['TMP_DIR'], str(object.id))
                    file_path = tmp_dir + '/' + object.filename
                    if not os.path.exists(tmp_dir):
                        os.makedirs(tmp_dir)
                    if not os.path.exists(file_path):
                        download(object, tmp_dir)
            else:
                response['message'] = 'Data object could not be found'
        except Exception as e:
            print('Exception ', e)
            print(traceback.format_exc())
            response['error'] = 1
            response['message'] = str(e)
            status = 500
        finally:
            if file_path is not None:
                return send_file(file_path, as_attachment=True, attachment_filename=object.filename)
            else:
                return response, status
    
    def post(self):
        return 'Only get request is allowed', 400   


def download(object, dest_dir):
    try:
        env = os.environ
        # Download the resulting data from the snakemake job.
        s3_client = boto3.client(
            's3',
            endpoint_url=env['S3_URL'],
            aws_access_key_id=env['S3_ACCESS_KEY_ID'],
            aws_secret_access_key=env['S3_SECRET_ACCESS_KEY']
        )
        s3_client.download_file(
            env['S3_BUCKET'], 
            'dvc/{0}/{1}/{2}'.format(object.pipeline_name, object.md5[:2], object.md5[2:]), 
            '{0}/{1}'.format(dest_dir, object.filename)
        )
    except Exception as e:
        print('Exception ', e)
        print(traceback.format_exc())