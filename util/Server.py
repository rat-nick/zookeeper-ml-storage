import logging
from kazoo.client import KazooClient, KazooState
from kazoo.exceptions import NodeExistsError
from .ClusterInfo import ClusterInfo
from .DataStorage import DataStorage
import requests

logging.basicConfig(level=logging.INFO)

class Server():
    """ Instance to manage zookeeper communication and synchronization """   
    def __init__(self, hostname, port):
        
        self.hostname = hostname
        self.port = port
        
        self.zk = KazooClient()
        self.cluster_info = ClusterInfo(self.zk)
        self.storage = DataStorage(self.zk)
        
        self.zk.start()
        self.setup() 

        @self.zk.ChildrenWatch('/live_nodes')
        def on_change(nodes):
            logging.info(f"Changes detected in live nodes...")
            logging.info(f"Updating cluster-info object on {self.hostname}:{self.port}...")
            self.cluster_info.update()
            logging.info(f'Cluster info:\nLive nodes:{self.cluster_info.live_nodes}\nMaster:{self.cluster_info.master}')
        
        @self.zk.ChildrenWatch('/election')
        def update_election(nodes):
            logging.info('Master change...')
            self.cluster_info.elect_leader()
            
        @self.zk.DataWatch('/master')
        def update_master(data, status):
            self.cluster_info.update()
            
        def disconnect_handler(state):
            if state == KazooState.LOST:
                logging.info("Connection lost")
                logging.info(f"{self.hostname}:{self.port}")
                # if I am the master
                if f"{self.hostname}:{self.port}" == self.zk.get('/election/master'):
                    self.zk.set("/master", b"None")    

        self.zk.add_listener(disconnect_handler)
        self.sync_with_master()
             
    def am_i_leader(self):
        #print(f'{self.hostname}:{self.port}')
        #print(self.cluster_info.master)
        return f'{self.hostname}:{self.port}' == self.cluster_info.master or self.cluster_info.master == None    
            
    def __del__(self):
        self.zk.stop()
              
    def setup(self):
        """Function to initialize a connection to the zookeeper service"""

        self.create_parrent_nodes()

        self.register_node()
        self.register_for_election()
        self.register_as_live()

    def register_for_election(self):
        val = f'{self.hostname}:{self.port}'
        logging.info(val)
        self.zk.create(
            '/election/node-', 
            value=val.encode(),
            ephemeral=True, sequence=True)
    
    def register_node(self):
        self.zk.ensure_path(str(f'/all_nodes/{self.hostname}:{self.port}'))

    def create_parrent_nodes(self):
        if not self.zk.exists('/election'):
            self.zk.create('/election')
        if not self.zk.exists('/master'):
            self.zk.create('/master')
            self.zk.set("/master", f'{self.hostname}:{self.port}'.encode())  
        if not self.zk.exists('/live_nodes'):
            self.zk.create('/live_nodes')
        if not self.zk.exists('/all_nodes'):
            self.zk.create('/all_nodes')
                    
    def register_as_live(self):
        try:
            self.zk.create(f"/live_nodes/{self.hostname}:{self.port}", ephemeral=True)
        except NodeExistsError:
            pass
    
    def get_model(self, id):
        model = self.storage.get_model(id)
        return model
    
    def set_model(self, model, id):
        # if I am the leader, update data and broadcast to other nodes
        if self.am_i_leader():
            self.storage.set_model(id, model)
            nodes = self.zk.children('/live_nodes')
            for node in nodes:
                # skip self
                if node == f'{self.server}:{self.port}':
                    continue
                # broadcast changes to other nodes
                data = {
                    'id' : id,
                    'model' : model
                }
                headers_dict = {"Update-From-Master": True}         
                requests.put(node, data=data, headers=headers_dict)
        
        # else send request to the leader
        else:
            data = {
                'id' : id,
                'model' : model
            }
            master = self.cluster_info.master
            requests.put(f'http://{master}', data=data)    
    
    def sync_with_master(self):
        if self.am_i_leader():
            return     
        else:
            self.cluster_info.update()
            master = self.cluster_info.master
            logging.info(f'master is {master}')
            res = requests.get(f'http://{master}/models/all')
            logging.info(res.json())
            
            self.storage.set_models(res.json())