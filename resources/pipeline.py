import traceback
from flask_restful import Resource
from flask import request
from db.models.snakemake_data_object import SnakemakeDataObject
from db.models.snakemake_pipeline import SnakemakePipeline

'''
Lists available pipelines (name and github repo).
For pipelines to be available, 
it needs to have successfully run at least once (have a completed data object)
'''
class ListPipeline(Resource):
    
    def get(self):
        status = 200
        response = {
            'pipelines': []
        }
        try:
            pipelines = SnakemakePipeline.objects()
            response['pipelines'] = SnakemakePipeline.serialize_list(pipelines)
        except Exception as e:
            print('Exception ', e)
            print(traceback.format_exc())
            response['error'] = 1
            response['message'] = str(e)
            status = 500
        finally:
            return response, status
    
    def post(self):
        return 'Only get request is allowed', 400