import base64

def serialize(data):
    return base64.b64encode(data)

def deserialize(data):
    return base64.b64decode(data)