import logging
from kazoo.exceptions import NoNodeError, NodeExistsError


class ClusterInfo():
    def __init__(self, zk_client):
        self.all_nodes = []
        self.live_nodes = []
        self.master = None
        self.zk = zk_client 
    
    def update(self):
        self.all_nodes = self.zk.get_children('/all_nodes')
        self.live_nodes = self.zk.get_children('/live_nodes')
        self.master = self.get_leader().decode()
        
    def get_leader(self):
        """Return leader data"""
        data, stat = self.zk.get('/master')
        #logging.info("Collecting leader data...")
        #logging.info("Version: %s, data: %s" % (stat.version, data.decode("utf-8")))
        return data
        
    def elect_leader(self):
        nodes = self.zk.get_children('/election')
        nodes.sort()
        master = self.zk.get(f'/election/{nodes[0]}')[0].decode()
        #logging.info(f'Master should be {master}')
        try:
            self.zk.set(
                '/master', 
                value=f'{master}'.encode())
        except NoNodeError:
            logging.info("No master node. Creating now...")
            try:
                self.zk.create(
                    '/master', 
                    value=f'{master}'.encode())
            except NodeExistsError:
                logging.info("Node already exists")
        finally:
            return master