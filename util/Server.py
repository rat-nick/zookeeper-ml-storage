import logging
from kazoo.client import KazooClient
from kazoo.exceptions import NodeExistsError
import requests


logging.basicConfig(level=logging.INFO)

class Server():
    """ Instance to manage zookeeper communication and synchronization """   
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        
        self.storage = DataStorage(self)
        self.zk = KazooClient()
        self.cluster_info = ClusterInfo(self.zk)
        self.zk.start()
        self.setup()
        
        @self.zk.ChildrenWatch('/live_nodes')
        def on_change(nodes):
            logging.info(f"Updating cluster-info object on {self.hostname}:{self.port}...")
            self.cluster_info.update()
            logging.info(f'Cluster info:\nLive nodes:{self.cluster_info.live_nodes}\nMaster:{self.cluster_info.master}')
        
    def am_i_leader(self):
        return f'{self.server}:{self.port}' == self.cluster_info.master     
            
    def __del__(self):
        self.zk.stop()
              
    def setup(self):
        """Function to initialize a connection to the zookeeper service"""

        self.create_parrent_nodes()

        self.register_node()
        self.register_for_election()
        self.register_as_live()

    def register_for_election(self):
        self.zk.create(
            f'/election/node-', 
            value=bytes(f'{self.hostname}:{self.port}', 
            encoding='utf-8'),
            ephemeral=True, sequence=True)

    def register_node(self):
        self.zk.ensure_path(str(f'/all_nodes/{self.hostname}:{self.port}'))

    def create_parrent_nodes(self):
        if not self.zk.exists('/election'):
            self.zk.create('/election')
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
                if node == f'{self.server}:{self.port}':
                    continue
                # broadcast changes to other nodes
                data = {
                    'id' : id,
                    'model' : model
                }
                headers_dict = {"Update-From-Leader": True}         
                requests.put(node, data=data, headers=headers_dict)
        
        # else send request to the leader
        else:
            data = {
                'id' : id,
                'model' : model
            }
            master = self.cluster_info.master
            requests.put(master, data=data)    
    
    def sync_with_master(self):
        if self.am_i_leader():
            return     
        else:
            models = requests.get(f'{self.cluster_info.master}')
            self.storage.set_models(models)    

class DataStorage():
    def __init__(self, zk):
        self.models = {}
        self.zk = zk
    
    def set_model(self, id, model):
        self.model_list[id] = model
    
    def set_models(self, models):
        self.models = models
        
    def get_model(self, id):
        return self.model_list[id]
    
    def get_all_models(self):
        return self.models
    
class ClusterInfo():
    def __init__(self, zk_client):
        self.all_nodes = []
        self.live_nodes = []
        self.master = None
        self.zk = zk_client 
    
    def update(self):
        self.all_nodes = self.zk.get_children('/all_nodes')
        self.live_nodes = self.zk.get_children('/live_nodes')
        self.master = self.get_leader_data()
        
    def get_leader_data(self):
        """Return leader data"""
        nodes = self.zk.get_children('/election')
        nodes.sort()
        master = self.zk.get(f'/election/{nodes[0]}')[0]
        return master 