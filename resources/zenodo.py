import os, threading, traceback, json, requests, shutil
from flask_restful import Resource
from flask import request
from db.models.snakemake_data_object import SnakemakeDataObject
from resources.data_object import download
from decouple import config
from util.check_token import check_token
from util.zenodo_functions.upload import upload
from util.zenodo_functions.upload_new_version import upload_new_version

class ZenodoUpload(Resource):
    method_decorators = [check_token]

    def get(self):
        return "Only post request is allowed", 400
    
    def post(self):
        status = 200
        response = {}
        try:
            req_body = request.get_json()
            data_obj_id = req_body.get('data_obj_id')
            deposition_id = req_body.get('deposition_id')
            object = None

            if(data_obj_id is not None):
                object = SnakemakeDataObject.objects(pk=data_obj_id).first()

            if(object is not None):
                if object.status.value == 'complete':
                    print('upload')
                    # execute the upload process in a separate thread
                    thread = threading.Thread(
                        target=fetch_and_upload, 
                        args=[object, deposition_id]
                    )
                    thread.start()
                    response['message'] = 'Object is being uploaded.'
                elif object.status.value == 'processing':
                    response['message'] = 'Unable to upload. Data object is being processed.'
                elif object.status.value == 'uploaded':
                    response = {
                        'message': 'Data object has already been uploaded.',
                        'doi': object.doi,
                        'download_link': object.download_link
                    }
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

'''
Downloads the data objects to temp dir, save it with the object filename.
Uploads the data object to Zenodo.
Updates the database document status as 'uploaded'.
'''
def fetch_and_upload(object, deposition_id=None):
    try:
        tmp_dir = os.path.join(config('TMP_DIR'), str(object.id))
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)

        # download data object from the object storage
        download(object, tmp_dir)
        print('download complete')

        # upload to Zenodo
        result = None
        if deposition_id is None:
            print('upload to new repo')
            result = upload(object, tmp_dir)
        else:
            print('upload new version')
            result = upload_new_version(deposition_id, object, tmp_dir)

        # update the database
        if result is not None and result['publish']:
            object.update(
                status='uploaded',
                doi=result['doi'],
                download_link=result['download_link']
            )
        shutil.rmtree(tmp_dir)
    except Exception as e:
        print('Exception ', e)
        print(traceback.format_exc())
