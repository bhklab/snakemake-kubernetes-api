import os, threading, traceback, json, requests
from flask_restful import Resource
from flask import request
from db.models.snakemake_data_object import SnakemakeDataObject
from resources.data_object import download
from decouple import config

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
                if object.status.value == 'complete':
                    print('upload')
                    # execute the upload process in a separate thread
                    thread = threading.Thread(
                        target=fetch_and_upload, 
                        args=[object]
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
def fetch_and_upload(object):
    try:
        tmp_dir = '{0}/{1}'.format(config('TMP_DIR'), str(object.id))
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)

        # download data object from the object storage
        download(object, tmp_dir)
        print('download complete')

        # upload to Zenodo
        result = upload(object, tmp_dir)
        print(result)

        # update the database
        if result['publish']:
            object.update(
                status='uploaded',
                doi=result['doi'],
                download_link=result['download_link']
            )

    except Exception as e:
        print('Exception ', e)
        print(traceback.format_exc())

def upload(object, source_dir):
    data = {
        'create_repo': False,
        'add_metadata': False,
        'upload': False,
        'publish': False
    }
    try:
        # Create repository
        BASE_URL = config('ZENODO_URL')
        ACCESS_TOKEN = config('ZENODO_ACCESS_TOKEN')
        res = requests.post(
            BASE_URL + '/api/deposit/depositions',
            params={'access_token': ACCESS_TOKEN}, json={},
            headers={"Content-Type": "application/json"}
        )
        print('create repo: %s' % res.status_code)
        result = res.json()
        bucket_url, deposition_id = None, None
        if res.status_code == 201:
            bucket_url = result['links']['bucket']
            deposition_id = result['id']
            data['doi'] = result['metadata']['prereserve_doi']['doi']
            data['create_repo'] = True
        else:
            data['error'] = result

        if data['create_repo']:
            # Add metadata
            metadata = {
                'metadata': {
                    'title': object.pipeline.name,
                    'upload_type': 'dataset',
                    'description': object.pipeline.name + ' data object generated by ORCESTRA.',
                    'creators': [{'name': 'Haibe-Kains, Benjamin','affiliation': 'Zenodo'}]
                }
            }
            res = requests.put(
                BASE_URL + '/api/deposit/depositions/%s' % deposition_id, 
                params={'access_token': ACCESS_TOKEN}, 
                data=json.dumps(metadata),
                headers={"Content-Type": "application/json"}
            )
            print('add metadata: %s' % res.status_code)
            if res.status_code == 200:
                data['add_metadata'] = True
            else:
                data['error'] = res.json()

        if data['add_metadata']:
            # Upload
            res = None
            with open('{0}/{1}'.format(source_dir, object.pipeline.object_name), 'rb') as fp:
                res = requests.put(
                    bucket_url + '/' + object.pipeline.object_name,
                    data=fp,
                    params={'access_token': ACCESS_TOKEN}
                )
            print('upload data: %s' % res.status_code)
            if res.status_code == 200:
                data['download_link'] = BASE_URL + "/record/" + str(deposition_id) + "/files/" + object.pipeline.object_name + "?download=1"
                data['upload'] = True
            else:
                data['error'] = res.json()

        if data['upload']:
            # Publish
            res = requests.post(
                BASE_URL + '/api/deposit/depositions/' + str(deposition_id) + '/actions/publish',
                params={'access_token': ACCESS_TOKEN} 
            )
            print('publish: %s' % res.status_code)
            if res.status_code == 202:
                data['publish'] = True
            else:
                data['error'] = res.json()
    except Exception as e:
        print('Exception ', e)
        print(traceback.format_exc())
    finally:
        return data