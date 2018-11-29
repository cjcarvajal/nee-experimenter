# -*- coding: utf-8 -*-
import pymongo
import json
import requests
import unidecode
import ner

remote_mongo_url = 'mongodb://negra:jamaicanGirl@ec2-34-212-201-251.us-west-2.compute.amazonaws.com/nee_experiment'
client = pymongo.MongoClient(remote_mongo_url)
db = client.nee_experiment

standfor_model_url = 'http://localhost:9000/'
stanford_properties_map = {'annotators':'ner','outputFormat':'json'}
stanford_params_map = {'properties': json.dumps(stanford_properties_map), 'pipelineLanguage': 'es'}

vision_model = ner.SocketNER(host='localhost', port=9191)

def evaluate():

	stanford_metrics = {}
	vision_metrics = {}

	tagged_tweets = db.tweets.find({'$and':[{'nee_entities':{'$exists':True}}]})

	for tweet in tagged_tweets:
		text = getText(tweet)

		entities_by_stanford = classyfyWithStanford(text)
		entities_by_vision = classifyWithVision(text)

		update_metrics(tweet['nee_entities'],entities_by_stanford,stanford_metrics)
		update_metrics(tweet['nee_entities'],entities_by_vision,vision_metrics)

	print_results(stanford_metrics,vision_metrics)

def getText(tweet):
	if 'retweeted_status' in tweet:
		return tweet['retweeted_status']['full_text']
	else:
		return tweet['full_text']

def classyfyWithStanford(text):
	r = requests.post(standfor_model_url, params=stanford_params_map, data=text.encode('utf-8'))
	result = r.json()['sentences'][0]['entitymentions']
	return [{'type':entity['ner'],'text':entity['text']} for entity in result]

def classifyWithVision(text):
	normalized_list = []
	result = vision_model.get_entities(text)

	for key in result:
		for entity in result[key]:
			item = {'type':key,'text':entity}
			normalized_list.append(item)
	return normalized_list

def update_metrics(expected_entities,obtained_entities,metrics):
	for expected_entity in expected_entities:
		founded_element = getEntityFromList(expected_entity,obtained_entities)
		if(founded_element is not None):
			if expected_entity['type'] in metrics:
				metrics[expected_entity['type']]['tp'] += 1
			else:
				metrics[expected_entity['type']] = {'tp':1,'fp':0,'fn':0}
			obtained_entities.remove(founded_element)
		else:
			if expected_entity['type'] in metrics:
				metrics[expected_entity['type']]['fn'] += 1
			else:
				metrics[expected_entity['type']] = {'tp':0,'fp':0,'fn':1}

	for obtained_entity in obtained_entities:
		if obtained_entity['type'] in metrics:
			metrics[obtained_entity['type']]['fp'] += 1
		else:
			metrics[obtained_entity['type']] = {'tp':0,'fp':1,'fn':0}

def getEntityFromList(entity,entity_list):
	for item in entity_list:
		if item['type'] == entity['type'] and item['text'] == entity['text']:
			return item
	return None

def print_results(stanford_metrics,vision_metrics):
	print stanford_metrics
	print vision_metrics

evaluate()


