import json
import logging
from util.Serializer import deserialize, serialize
logging.basicConfig(level=logging.INFO)




class DataStorage():


    def __init__(self, zk):
        self.models = {}
        self.zk = zk
    
    def set_model(self, id, model):
        self.models[int(id)] = model
        logging.info(f"Storage: Saving model {model[0:50]}")
        #logging.debug(f"Keys are {self.get_all_keys()}")
    
    def set_models(self, models):
        for k in models.keys():
            self.models[int(k)] = models[k]
                    
    def get_model(self, id):    
        return self.models[int(id)]
    
    def get_all_models(self):
        return self.models
    
    def get_num_models(self):
        return len(self.models.keys())