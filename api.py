from flask import Flask, request
from flask_restx import Api, Resource, reqparse
import werkzeug
import pickle
import optparse

parser = optparse.OptionParser()
parser.add_option('-p', '--port', action='store', help='port to listen on')
options, args = parser.parse_args()
print(options.port)
port = int(options.port)

app = Flask(__name__)
api = Api(app)

ns = api.namespace('models', description='model operations')

get_parser = reqparse.RequestParser()
get_parser.add_argument('vars', type=list, action='store_true',)

put_parser = reqparse.RequestParser()
put_parser.add_argument('modelfile', type=werkzeug.datastructures.FileStorage, location='files')

models = dict()
@ns.route('/<int:id>')
class Model(Resource):
        
    @api.expect(get_parser)
    def get(self,id):
        
        model = pickle.loads(models[id])
        vars = get_parser.parse_args()['vars']
        print(vars)
        return {
            'status' : 200,
            'preduction': model.predict(vars)
        }
    @api.expect(put_parser)
    def put(self, id):
        modelfile = put_parser.parse_args()['modelfile']
        model, _, __, ___ = pickle.load(modelfile)
        models[id] = model
        return{
            "status": 200,
            #'model' : str(models[id])
        }

ns = api.namespace('cluster-info', description='cluster-info sync')

@ns.route("/")
class ClusterInfo(Resource):
    def get(self):
        return {'cluster-info': 'ok'}
    
if __name__ == '__main__':
    app.run(debug=True, port=port)