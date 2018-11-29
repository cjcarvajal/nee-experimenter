# -*- coding: utf-8 -*-
import pymongo
import json
import requests
import unidecode
import ner
import sys

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

	print_results(stanford_metrics)
	print_results(vision_metrics)

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

result = {u'CITY': {'fp': 34, 'fn': 75, 'tp': 69}, u'CAUSE_OF_DEATH': {'fp': 14, 'fn': 2, 'tp': 2}, u'NATIONALITY': {'fp': 3, 'fn': 18, 'tp': 4}, u'TITLE': {'fp': 79, 'fn': 146, 'tp': 118}, u'PERCENT': {'fp': 2, 'fn': 2, 'tp': 2}, u'COUNTRY': {'fp': 6, 'fn': 13, 'tp': 69}, u'RELIGION': {'fp': 3, 'fn': 1, 'tp': 1}, u'MISC': {'fp': 70, 'fn': 280, 'tp': 10}, u'NUMBER': {'fp': 57, 'fn': 42, 'tp': 50}, u'MONEY': {'fp': 13, 'fn': 37, 'tp': 0}, u'PERSON': {'fp': 102, 'fn': 283, 'tp': 156}, u'IDEOLOGY': {'fp': 14, 'fn': 24, 'tp': 1}, u'LOCATION': {'fp': 63, 'fn': 24, 'tp': 1}, u'CRIMINAL_CHARGE': {'fp': 14, 'fn': 374, 'tp': 1}, u'DATE': {'fp': 21, 'fn': 20, 'tp': 2}, u'ORGANIZATION': {'fp': 260, 'fn': 258, 'tp': 222}, u'STATE_OR_PROVINCE': {'fp': 1, 'fn': 1, 'tp': 1}}

def print_results(metrics):
	tp_total = 0
	fp_total = 0
	fn_total = 0
	print 70*'-'
	cols_format = "{:>18} {:<10} {:<10} {:<10} {:<5} {:<5} {:<5}\n"
	sys.stdout.write(cols_format.format('Entity','P','R','F1','TP', 'FP','FN'))
	for key in metrics:
		tp = metrics[key]['tp']
		fp = metrics[key]['fp']
		fn = metrics[key]['fn']

		tp_total += tp
		fp_total += fp
		fn_total += fn 

		precision = calc_precision(tp,fp)
		recall = calc_recall(tp,fn)
		f1 = calc_F1(precision,recall)

		sys.stdout.write(cols_format.format(key,round(precision,8),round(recall,8),round(f1,8),tp,fp,fn))

	precision = calc_precision(tp_total,fp_total)
	recall = calc_recall(tp_total,fn_total)
	f1 = calc_F1(precision,recall)

	sys.stdout.write(cols_format.format('TOTAL',round(precision,8),round(recall,8),round(f1,8),tp_total,fp_total,fn_total))
	print 70*'-'
	print '\n'

def calc_precision(tp,fp):
	if tp == 0 and fp == 0:
		return 0
	else:
		return float(tp)/(float(tp + fp))

def calc_recall(tp,fn):
	if tp == 0 and fn == 0:
		return 0
	else:
		return float(tp)/(float(tp + fn))


def calc_F1(precision,recall):
	if precision == 0 and recall == 0:
		return 0
	else:
		return 2*(precision*recall)/(precision+recall)

evaluate()
