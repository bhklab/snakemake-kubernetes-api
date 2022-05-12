import os, subprocess, traceback, re
from flask_restful import Resource
from flask import request

class K8ErrorPods(Resource):
    def get(self):
        status = 200
        response = {}
        try:
            k8_process = subprocess.Popen(["kubectl", "get", "pods"], stdout=subprocess.PIPE)
            stdout, std_err = k8_process.communicate()
            pods = re.split(r'\n+', stdout.decode('ascii'))
            r = re.compile("snakejob.*")
            pods = list(filter(r.match, pods))
            response['pods'] = pods
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


class K8ErrorLog(Resource):
    def get(self):
        status = 200
        response = {}
        podname = None
        try:
            podname = request.args.get('podname')
            if podname is not None:
                k8_process = subprocess.Popen(["kubectl", "logs", podname], stdout=subprocess.PIPE)
                stdout, std_err = k8_process.communicate()
                response['log'] = stdout.decode('ascii')
            else:
                response['message'] = 'Missing pod name.'
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
