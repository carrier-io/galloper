from flask_restful import Resource


class forwardAuth(Resource):
    def get(self):
        return {
            'groups': ['/grafana', '/superadmin'],
            'username': 'user'
        }


class token(Resource):
    def get(self):
        return {
            "message": "Create a secret called auth_token by yourself"
        }
