import traceback
from flask_restful import Resource
from flask import request

class ListLogs(Resource):
    def get(self):
        status = 200
        response = {}
        try:
            print('list logs')
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
        try:
            print('get log')
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