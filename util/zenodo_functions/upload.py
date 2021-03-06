import traceback, json, requests
from decouple import config

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