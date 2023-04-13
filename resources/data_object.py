import os
import traceback
import boto3
from decouple import config
from flask_restful import Resource
from flask import request, send_file
from db.models.snakemake_data_object import SnakemakeDataObject
from db.models.snakemake_pipeline import SnakemakePipeline


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
            query = {}
            status = request.args.get('status')
            pipeline_name = request.args.get('pipeline_name')
            latest = request.args.get('latest')
            if status is not None:
                query['status'] = status
            if pipeline_name is not None:
                pipeline = SnakemakePipeline.objects(
                    name=pipeline_name).first()
                if pipeline is not None:
                    query['pipeline'] = pipeline.pk

            objects = SnakemakeDataObject.objects.filter(
                **query).order_by('-id')

            if latest:
                response['object'] = objects[0].serialize()
            else:
                response['objects'] = SnakemakeDataObject.serialize_list(
                    objects)
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
        object = None
        file_path = None
        try:
            data_obj_id = request.args.get('data_obj_id')
            if (data_obj_id is not None):
                object = SnakemakeDataObject.objects(pk=data_obj_id).first()

            if (object is not None):
                if object.status.value == 'processing':
                    response['message'] = 'Unable to download. Data object is being processed.'
                else:
                    tmp_dir = '{0}/{1}'.format(config('TMP_DIR'),
                                               str(object.id))
                    file_path = tmp_dir + '/' + object.pipeline.object_name
                    if not os.path.exists(tmp_dir):
                        os.makedirs(tmp_dir)
                    if not os.path.exists(file_path):
                        download(
                            object.pipeline.name,
                            object.pipeline.object_name,
                            object.md5,
                            tmp_dir
                        )
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
                return send_file(file_path, as_attachment=True, attachment_filename=object.pipeline.object_name)
            else:
                return response, status

    def post(self):
        return 'Only get request is allowed', 400


def download(pipeline_name, object_name, md5, dest_dir):
    try:
        # Download the resulting data from the snakemake job.
        s3_client = boto3.client(
            's3',
            endpoint_url=config('S3_URL'),
            aws_access_key_id=config('S3_ACCESS_KEY_ID'),
            aws_secret_access_key=config('S3_SECRET_ACCESS_KEY')
        )
        s3_client.download_file(
            config('S3_BUCKET'),
            'dvc/{0}/{1}/{2}'.format(pipeline_name, md5[:2], md5[2:]),
            os.path.join(dest_dir, object_name)
        )
    except Exception as e:
        print('Exception ', e)
        print(traceback.format_exc())
