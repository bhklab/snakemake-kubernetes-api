import os, traceback
from flask_restful import Resource
from flask import request, send_file
from decouple import config

class ListLogs(Resource):
    def get(self):
        status = 200
        response = {
            "logs": []
        }
        try:
            path = None
            pipeline = request.args.get('pipeline')
            response['pipeline'] = pipeline
            if pipeline is not None:
                path = os.path.join(config('SNAKEMAKE_ROOT'), pipeline + '-snakemake', '.snakemake/log')
            if path is not None and os.path.exists(path):
                logs = os.listdir(path)
                logs.sort(reverse=True)
                response['logs'] = logs
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

class DownloadLog(Resource):
    def get(self):
        status = 200
        response = {}
        file_path = None
        filename = None
        try:
            pipeline = request.args.get('pipeline')
            filename = request.args.get('filename')
            if pipeline is not None and filename is not None:
                path = os.path.join(config('SNAKEMAKE_ROOT'), pipeline + '-snakemake', '.snakemake/log', filename)
                if os.path.isfile(path):
                    file_path = path 
                else:
                    response['message'] = 'The requested log file does not exist.' 
            else:
                response['message'] = 'Missing pipeline name and/or log filename.'
        except Exception as e:
            print('Exception ', e)
            print(traceback.format_exc())
            response['error'] = 1
            response['message'] = str(e)
            status = 500
        finally:
            if file_path is not None:
                return send_file(file_path, as_attachment=True, attachment_filename=filename)
            else:
                return response, status
    
    def post(self):
        return 'Only get request is allowed', 400    

 