class DataStorage():
    def __init__(self, zk):
        self.models = {}
        self.zk = zk
    
    def set_model(self, id, model):
        self.models[id] = model
    
    def set_models(self, models):
        self.models = models
        
    def get_model(self, id):
        return self.models[id]
    
    def get_all_models(self):
        return self.models