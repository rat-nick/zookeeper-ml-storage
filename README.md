# zookeeper-ml-storage

A homework assignment on the subject of cloud computing. The assignment was to design an RESTful API for storing, 
updating and reading machine learning models for the purpose of predicting values. The API should function as a cluster of servers 
where there is a master and worker nodes. The master node should be handling all the PUT requests while any node is capable of handling
GET request.

The purpose of the assignment was for the student to get to know the [apache-zookeeper](https://zookeeper.apache.org/) service, and solve
various problems concerning maintaining the consistency of data and configuration values throughout the cluster, all while handling server failure
and master node re-election.

The implementation is in python, because it was easy to use the machine learning libraries and the pickle module for easy serialization and
deserialization of trained models.

## Requirements
- [zookeeper](https://zookeeper.apache.org/)
- [python](https://www.python.org/)

## Usage

1. Before running the api, run `pip install -r requirements.txt`
2. Start the zookeeper server on the local machine.
3. Run `python api.py -s <hostname> -p <port>`

### Note
Make sure that you are running multiple instances of the api on different ports to test out all the fuctions of the api. 
