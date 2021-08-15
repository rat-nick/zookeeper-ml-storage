from flask import Flask, request
from flask_restx import Api, Resource, reqparse
import werkzeug
import pickle
import optparse
from util.Server import Server

# defining command line arguments
parser = optparse.OptionParser()
parser.add_option('-p', '--port', action='store', help='port to listen on')
parser.add_option('-s', '--server', action='store', help='server')

# collecting command line arguments
options, args = parser.parse_args()
port = int(options.port)
server = options.server

# setting up 
zkServer = Server(server, port)
app = Flask(__name__)
api = Api(app)

ns = api.namespace('models', description='model operations')

get_parser = reqparse.RequestParser()
get_parser.add_argument('vars', type=list, action='store_true')

put_parser = reqparse.RequestParser()
put_parser.add_argument('modelfile', type=werkzeug.datastructures.FileStorage, location='files')



@ns.route('/<int:id>')
class Model(Resource):        
    @api.expect(get_parser)
    def get(self,id):
        
        vars = get_parser.parse_args()['vars']
        print(vars)
        
        zkServer.get_model(id)
        return {
            'status' : 200,
            'prediction': "prediction"
        }
        
    @api.expect(put_parser)
    def put(self, id):
        if not request.headers.contains('Update-From-Master'):  
            return
        modelfile = put_parser.parse_args()['modelfile']
        model, _, __, ___ = pickle.load(modelfile)
        
        return{
            "status": 200,
            #'model' : str(models[id])
        }

ns = api.namespace('cluster-info', description='cluster-info sync')
@ns.route("/")
class ClusterInfo(Resource):
    def get(self):
        return str(zkServer.cluster_info)
    
    
def main():
    app.run(debug=True, port=port)
    
if __name__ == '__main__':
    main()