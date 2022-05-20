from flask_restful import Resource
# from util.check_token import check_token


class Test(Resource):
    # method_decorators = [check_token]
    def get(self):
        return 'ok'
    
    def post(self):
        return 'ok'