#!flask/bin/python
from flask import Flask, json, request
from flask_cors import CORS, cross_origin
import pymongo
import requests

remote_mongo_url = 'mongodb://negra:jamaicanGirl@ec2-34-212-201-251.us-west-2.compute.amazonaws.com/nee_experiment'
client = pymongo.MongoClient(remote_mongo_url)
db = client.nee_experiment

app = Flask(__name__)
CORS(app,resources=r'/*')

in_session_ids = []

@app.route('/help',methods=['GET'])
def get_untagged_tweet():

	if len((in_session_ids)) > 10:
		in_session_ids[:] = []
	
	data = db.tweets.find_one({'$and':[
		{'nee_entities':{'$exists':False}},
		{'id':{'$nin':in_session_ids}}
		]}
		)
	in_session_ids.append(data['id'])
	response = {}

	if 'retweeted_status' in data:
		response['text'] = data['retweeted_status']['full_text']
	else:
		response['text'] = data['full_text']	

	response['id'] = str(data['id'])
	return json.dumps(response,ensure_ascii=False),200

@app.route('/help/another',methods=['POST'])
def replace_tweet():

	undesired_tweets_ids = request.json['ids']

	data = db.tweets.find_one({'$and':[
		{'nee_entities':{'$exists':False}},
		{'id':{'$nin':[long(id) for id in undesired_tweets_ids]}}]})

	response = {}
	response['id'] = str(data['id'])
	response['text'] = data['full_text']
	return json.dumps(response,ensure_ascii=False),200

@app.route('/help/mark',methods=['POST'])
def mark_tweet():

	tweet_id = request.json['id']
	entities_list = request.json['entities']
	defender = request.json['defender']

	db.tweets.update_one(
      { 'id':long(tweet_id) },
      { '$set': { "nee_entities" : entities_list}});

	db.defenders.insert({'name':defender,'tweet_id':tweet_id})

	return 'Done',200

@app.route('/help/mark/empty',methods=['POST'])
def mark_tweet_as_empty():
	tweet_id = request.json['id']
	defender = request.json['defender']
	entities_list = {}

	db.tweets.update_one(
      { 'id':long(tweet_id) },
      { '$set': { "nee_entities" : entities_list}});

	db.defenders.insert({'name':defender,'tweet_id':tweet_id})

	return 'Done',200

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8089)