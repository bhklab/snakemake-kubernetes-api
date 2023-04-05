import traceback, json, requests
from decouple import config
from util.zenodo_functions.upload_file import upload_file

"""
Function to upload data object to new repository on Zenodo
"""
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
            if object.object_files is not None:
                results = list()
                for object_file in object.object_files:
                    result = upload_file(
                        source_dir,
                        object_file['filename'],
                        BASE_URL,
                        bucket_url,
                        ACCESS_TOKEN,
                        deposition_id
                    )
                    uploaded = {
                        'filename': object_file['filename']
                    }
                    if result.get('error') is None:
                        data['upload'] = True
                        uploaded['download_link'] = result.get('download_link')
                    else:
                        data['upload'] = False
                        uploaded['error'] = result.get('error')
                    results.append(uploaded)
                data["uploaded_files"] = results
            else:
                result = upload_file(
                    source_dir,
                    object.pipeline.object_name,
                    BASE_URL,
                    bucket_url,
                    ACCESS_TOKEN,
                    deposition_id
                )
                if result.get('error') is None:
                    data['upload'] = True
                    data['download_link'] = result.get('download_link')
                else:
                    data['error'] = result.get('error')

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