import traceback, json, requests
from decouple import config
from util.zenodo_functions.upload_file import upload_file

"""
Function to create a new version of the existing repository and uploads an updated data object.
"""
def upload_new_version(deposition_id, object, source_dir):
    data = {
        'create_new_version': False,
        'remove_old_file': False,
        'upload_new_file': False,
        'publish': False
    }
    try:
        BASE_URL = config('ZENODO_URL')
        ACCESS_TOKEN = config('ZENODO_ACCESS_TOKEN')
        # create new version
        res = requests.post(
            BASE_URL + '/api/deposit/depositions/' + deposition_id + '/actions/newversion',
            params={'access_token': ACCESS_TOKEN},
            headers={"Content-Type": "application/json"}
        )
        print('create new version: %s' % res.status_code)
        new_version = res.json()
        draft_url = None
        file_found = None
        if res.status_code == 201:
            data['create_new_version'] = True
            draft_url = new_version.get('links').get('latest_draft')
        else:
            data['error'] = new_version

        # delete existing file
        new_deposition = None
        if data['create_new_version']:
            res = requests.get(
                draft_url,
                params={'access_token': ACCESS_TOKEN},
                headers={"Content-Type": "application/json"}
            )
            new_deposition = res.json()
            data['doi'] = new_deposition.get('doi')
            # file_found = next((item for item in new_deposition.get('files') if item["filename"] == object.pipeline.object_name), None)
            for file_found in new_deposition.get('files'):
                print('file to delete: ' + file_found['filename'])
                res = requests.delete(
                    draft_url + '/files/' + file_found['id'],
                    params={'access_token': ACCESS_TOKEN},
                    headers={"Content-Type": "application/json"}
                )
                if res.status_code == 204:
                    data['remove_old_file'] = True
                else:
                    data['error'] = res.json()

        # upload data
        if data['remove_old_file']:
            # Upload
            if object.object_files is not None:
                results = list()
                for object_file in object.object_files:
                    result = upload_file(
                        source_dir,
                        object_file['filename'],
                        BASE_URL,
                        new_deposition.get('links').get('bucket'),
                        ACCESS_TOKEN,
                        deposition_id
                    )
                    uploaded = {
                        'filename': object_file['filename']
                    }
                    if result.get('error') is None:
                        data['upload_new_file'] = True
                        uploaded['download_link'] = result.get('download_link')
                    else:
                        data['upload_new_file'] = False
                        uploaded['error'] = result.get('error')
                    results.append(uploaded)
                data["uploaded_files"] = results
            else:
                result = upload_file(
                    source_dir,
                    object.pipeline.object_name,
                    BASE_URL,
                    new_deposition.get('links').get('bucket'),
                    ACCESS_TOKEN,
                    deposition_id
                )
                if result.get('error') is None:
                    data['upload_new_file'] = True
                    data['download_link'] = result.get('download_link')
                else:
                    data['error'] = result.get('error')

        # publish new version
        if data['upload_new_file']:
            # Publish
            res = requests.post(
                new_deposition.get('links').get('publish'),
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