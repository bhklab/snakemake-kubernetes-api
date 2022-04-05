from flask_restful import Resource
from datetime import datetime
from db.models.snakemake_data_object import SnakemakeDataObject 

class Test(Resource):
    def get(self):
        SnakemakeDataObject(
            dataset_name = 'pdtx',
            filename = 'pdtx.rds',
            git_url = 'www.google.ca',
            commit_id = '1234567890',
            status = 'processing',
            process_start_date = datetime.now()
        ).save()
        return 'ok'