import logging
from typing import Text
from util.Serializer import deserialize, serialize
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, reqparse
import werkzeug
import pickle
import optparse
from util.Server import Server

logging.basicConfig(filename='server.log', encoding='utf-8',level=logging.INFO)


# defining command line arguments
parser = optparse.OptionParser()
parser.add_option('-p', '--port', action='store', help='port to listen on')
parser.add_option('-s', '--server', action='store', help='server')

# collecting command line arguments
options, args = parser.parse_args()
port = int(options.port)
server = options.server

# setting up 

app = Flask(__name__)
api = Api(app)
zkServer = Server(server, port)
ns = api.namespace('models', description='model operations')

get_parser = reqparse.RequestParser()
get_parser.add_argument('vars', type=str, action='store_true')

put_parser = reqparse.RequestParser()
put_parser.add_argument('model', type=werkzeug.datastructures.FileStorage, location='files')

@ns.route('/all')
@ns.hide
class AllModels(Resource):
    def get(self):
        res = zkServer.storage.get_all_models()
        #logging.info(f"all models:{res}")
        return zkServer.storage.get_all_models()

@ns.route('/<int:id>')
class Model(Resource):        
    @api.expect(get_parser)
    def get(self,id):
        vars = get_parser.parse_args()['vars']
        #logging.info(f"Input params: {vars}")
        vars = [float(x) for x in vars.split(',')]
        #logging.info(f"Input params: {vars}")
        
        try:
            model = zkServer.get_model(int(id))
            #logging.info(f"GET: model is {model}")
            #deserialize the model
            model = deserialize(model)
            #logging.info(f"Deserialized model is {model[0:20]}")
            model = pickle.loads(model)
            
            prediction = model.predict([vars])
            prediction = prediction.tolist()
            return {
                'status' : 200,
                'predictions': prediction
            }
        except KeyError as e:
            return {
                'status': 404,
                'numModels': zkServer.storage.get_num_models()
            }
        
        
    
    # this is seen from outside the platform on swaggerUI     
    @api.expect(put_parser)
    def put(self, id):
        
        # it is a request from the frontend
        if 'model' in request.files:
            modelfile = request.files['model']
            model, _, __, ___ = pickle.load(modelfile)
            model = str(serialize(model), 'utf-8')
            logging.info(f"FRNT serialized model as {model[0:50]}")
            zkServer.set_model(id, model)
            
            return {
                "status": 200,
            }
            
        # it is a request from other servers on backend    
        elif 'model' in request.form:
            model = request.form['model']
            logging.info(f"BCK:First byte {model[0:50]}")
            zkServer.set_model(id, model)
            return {
                "status": 200,
            }        
@api.route('/master-command')
@api.hide
class UpdateModel(Resource):
    def put(self):
        logging.info(f"PUT ON MASTER-COMMAND")
        if "Update-From-Master" in request.headers:
            model = request.form['model']
            logging.info(f"BCK: Master send model  {model[0:50]}")
            id = request.form['id']
            zkServer.storage.set_model(id, model)
            return {
                'status': 200,
            }
        return {
            'status' : 400
        }                
        
ns = api.namespace('cluster-info', description='cluster-info sync')
@ns.route("/")
class ClusterInfo(Resource):
    def get(self):
        return str(zkServer.cluster_info)
        
def main():
    app.run(debug=True, port=port, use_reloader=False)
    
if __name__ == '__main__':
    #zkServer = Server(server, port)
    main()