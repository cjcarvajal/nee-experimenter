import pymongo
import json
import os

root_path = '/Users/carlosj/Documents/Maestria/Tesis 1/Vision/NEE_Experimenter/tweets_bk_11_10_2018'
remote_mongo_url = 'mongodb://negra:jamaicanGirl@ec2-34-212-201-251.us-west-2.compute.amazonaws.com/nee_experiment'

def loadFile(file_path):
	with open(file_path) as data_file:
		file_str = data_file.read()
		file_str = '[' + file_str + ']'
		file_str = file_str.replace('}{','},{')
		return json.loads(file_str)

client = pymongo.MongoClient(remote_mongo_url)
db = client.nee_experiment

for file in os.listdir(root_path):
	print root_path + '/' + file
	tweets = loadFile(root_path + '/' + file)
	for batch in tweets:
		for status in batch['statuses']:
			db.tweets.insert_one(status)