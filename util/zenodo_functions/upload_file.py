import json, requests

def upload_file(source_dir, filename, base_url, bucket_url, access_token, deposition_id):
    print(filename)
    res = None
    data = {}
    with open('{0}/{1}'.format(source_dir, filename), 'rb') as fp:
        res = requests.put(
            bucket_url + '/' + filename,
            data=fp,
            params={'access_token': access_token}
        )
    print('upload data: %s' % res.status_code)
    if res.status_code == 200:
        data['download_link'] = base_url + "/record/" + str(deposition_id) + "/files/" + filename + "?download=1"
        data['upload'] = True
    else:
        data['error'] = res.json()
    return(data)