import traceback, boto3
from flask_restful import Resource
from flask import request
from db.models.snakemake_data_object import SnakemakeDataObject

class ZenodoUpload(Resource):

    def get(self):
        return "Only post request is allowed", 400
    
    def post(self):
        status = 200
        response = {}
        try:
            req_body = request.get_json()
            data_obj_id = req_body['data_obj_id'] if 'data_obj_id' in req_body.keys() else None
            object = None
            if(data_obj_id is not None):
                object = SnakemakeDataObject.objects(pk=data_obj_id).first()
            if(object is not None):
                match object.status:
                    case 'complete':
                        print('upload')
                        # download the data objects to temp dir, save it with the object filename.

                        # upload the data object to Zenodo

                        response['message'] = 'Object is being uploaded.' # get the pre-assigned doi.
                    case 'processing':
                        response['message'] = 'Unable to upload. Data object is being processed.'
                    case 'uploaded':
                        response['message'] = 'Data object has already been uploaded.' # get the doi.
            else:
                response['message'] = 'Data object could not be found'
        except Exception as e:
            print('Exception ', e)
            print(traceback.format_exc())
            response['error'] = 1
            response['message'] = str(e)
            status = 500
        finally:
            return response, status