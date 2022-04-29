import traceback
from flask_restful import Resource
from flask import request
from db.models.snakemake_data_object import SnakemakeDataObject

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
            objects = SnakemakeDataObject.objects(status='complete')
            
            pipelines = []
            pipeline_match = lambda pipeline: pipeline.pipeline_name == obj.pipeline_name and pipeline.git_url == obj.git_url
            for obj in objects:
                if (next(filter(pipeline_match, pipelines), None) is None):
                    pipelines.append(obj)
            
            pipelines = map(
                lambda pipeline: {
                    'pipeline_name': pipeline.pipeline_name, 
                    'git_url': pipeline.git_url
                }, pipelines
            )
            response['pipelines'] = list(pipelines)
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