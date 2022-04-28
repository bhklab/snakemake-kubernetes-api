import traceback
from flask_restful import Resource
from flask import request
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
        try:
            print('download')
        except Exception as e:
            print('Exception ', e)
            print(traceback.format_exc())
            response['error'] = 1
            response['message'] = str(e)
            status = 500
        finally:
            return response, status
    
    def post(self):
        return 'Only get request is allowed', 400   