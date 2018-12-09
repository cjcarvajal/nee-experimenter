# -*- coding: utf-8 -*-
from num2words import num2words
import pymongo
import os
import random
import subprocess
import spacy
import re

nlp = spacy.load('es')

#Parameters
training_percent = 0.7
not_entities_percent_length = 0.1;
number_in_string = True
money_entity_generator_limit = 10
money_entity_generator_max = 99

#Constants
regex_entities = r'.*\t(CITY|CAUSE_OF_DEATH|TITLE|COUNTRY|CRIMINAL_CHARGE|RELIGION|MISC|NUMBER|MONEY|PERSON|LOCATION|ORGANIZATION|DATE|NATIONALITY|PERCENT|IDEOLOGY)'
number_entity = 'NUMBER'
money_entity = 'MONEY'
currency_symbols = ['$']
currency_suffix_prefix = ['USD ','COP ','EUR']
currency_suffix = [' de dolares', ' de pesos', ' de euros']
money_multiples = [1000000,10000000,100000000,1000000000,10000000000,100000000000,1000000000000]

# Remove output previous files
os.system('rm training.tsv test.tsv')

remote_mongo_url = 'mongodb://negra:jamaicanGirl@ec2-34-212-201-251.us-west-2.compute.amazonaws.com/nee_experiment'
client = pymongo.MongoClient(remote_mongo_url)
db = client.nee_experiment

query_result = db.tweets.find( {'$and':[{'nee_entities':{'$exists':True}}]},{'_id':0,'full_text':1,'nee_entities':1})

punctuation = '!"#$%&\'\"()*+,-./:;<=>?[\\]^_`{|}~'		

training_file_items = []
test_file_items = []

def process_tweet(text,entities):
	token_list = [text]
	for entity in entities:
		dirty_entity = entity['text']
		clean_entity = dirty_entity.strip().lstrip(punctuation).rstrip(punctuation)
	
		for index,token in enumerate(token_list):
			if dirty_entity in token:
				splitted_text = token.split(clean_entity,1)
				if splitted_text[0]:
					token_list.insert(index,splitted_text[0])
					index += 1
				if index < len(token_list):
					token_list[index] = clean_entity + '\t' + entity['type']
				else:
					token_list.append(clean_entity + '\t' + entity['type'])
				if splitted_text[1]:
					index += 1
					if index < len(token_list):
						token_list.insert(index+2,splitted_text[1])
					else:
						token_list.append(splitted_text[1])
				break
	return token_list

def tokenize_lines(file_lines):
	tokenized_file_content = ''
	for line in file_lines:

		if not line.strip():
			continue
		
		if line:
			if not re.match(regex_entities,line):
				for token in nlp(line):
					if not token.text.strip():
						continue
					tokenized_file_content += token.text + '\tO\n'
			else:
				tokenized_file_content += line + '\n'
	return tokenized_file_content

total_length = query_result.count()
training_lenght = int(total_length * training_percent)
tweet_counter = 0

def add_money_entities(entity_list,entity):
	money_value = ''
	for nee_entity in entity['nee_entities']:
		if nee_entity['type'] == money_entity:
			money_value = nee_entity['text']

	if money_value:
		if money_entity_generator_limit > 0:
			randon_number = random.randint(1,number_entity_generator_limit)
			for multiple in money_multiples:
				money_number = randon_number * multiple
				number_in_string = num2words(randon_number * multiple, lang='es')

			for symbol in currency_symbols:
				replaced_value = symbol + str(money_number)
			for suf_pre in currency_suffix_prefix:
				replaced_value = suf_pre + number_in_string
			for suf in currency_suffix:
				replaced_value =number_in_string + suf

			money_entity_generator_limit -= 1

retrieved_list = list(query_result)

for item in retrieved_list:
	tweet_counter += 1
	full_text = item['full_text']
	entities = item['nee_entities']

	add_money_entities(retrieved_list,item)

	'''
	The order matters so the tweet text must be tokenized and classified following the
	same order for token as presented in the original tweet
	'''
	if tweet_counter < training_lenght:
		training_file_items.extend(process_tweet(full_text,entities))
	else:
		test_file_items.extend(process_tweet(full_text,entities))	

training_file_content = tokenize_lines(training_file_items)
test_file_content = tokenize_lines(test_file_items)

with open ('training.tsv','w') as total_data_file:
	total_data_file.write(training_file_content.encode('utf8'))

with open ('test.tsv','w') as total_data_file:
	total_data_file.write(test_file_content.encode('utf8'))

# Remove working files
# os.system('rm total_data')

