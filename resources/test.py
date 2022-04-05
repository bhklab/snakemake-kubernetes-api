from flask_restful import Resource
from datetime import datetime
from db.models.snakemake_data_object import SnakemakeDataObject 

class Test(Resource):
    def get(self):
        return 'ok'