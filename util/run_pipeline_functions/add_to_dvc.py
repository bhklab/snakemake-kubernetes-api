import os
import re
import subprocess
from decouple import config

# downloads data from the snakemake job and adds it to DVC
# returns md5 checksum for that data file
def add_to_dvc(s3_client, pipeline_name, filename, dvc_repo_name, alt_filename=None):
    stored_filename = alt_filename if alt_filename is not None else filename
    
    # Download the resulting data from the snakemake job.
    s3_client.download_file(
        config('S3_BUCKET'),
        'snakemake/{0}/{1}'.format(pipeline_name, stored_filename),
        os.path.join(config('DVC_ROOT'), dvc_repo_name, filename)
    )
    print('download complete')

    # Add data to DVC remote.
    cwd = os.path.abspath(os.getcwd())
    add_data_cmd = [
        'bash',
        os.path.join(cwd, 'bash', 'dvc_add.sh'),
        '-r', os.path.join(config('DVC_ROOT'), dvc_repo_name),
        '-d', pipeline_name,
        '-f', filename
    ]
    dvc_process = subprocess.Popen(
        add_data_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        line = dvc_process.stdout.readline()
        if not line:
            break
        else:
            print(line.rstrip().decode("utf-8"))
    with open(os.path.join(config('DVC_ROOT'), dvc_repo_name, filename + ".dvc")) as file:
        lines = [line.rstrip() for line in file]
    r = re.compile("^- md5:.*")
    found = next(filter(r.match, lines), None)
    md5 = None
    if found:
        md5 = re.findall(r'- md5:\s(.*?)$', found)
        print('data added: ' + md5[0])
    else:
        print('md5 not found')
    os.remove(os.path.join(config('DVC_ROOT'), dvc_repo_name, filename))
    return(md5[0])