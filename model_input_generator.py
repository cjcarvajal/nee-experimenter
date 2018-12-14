# -*- coding: utf-8 -*-
from num2words import num2words
import pymongo
import os
import random
import subprocess

#Parameters
training_percent = 0.7
not_entities_percent_length = 0.1;

number_entity_generator_limit = 100
number_repetition_factor = 1
number_in_string = True

money_entity_generator_limit = 10
money_entity_generator_max = 99


#Constants
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

entities_file_content = ''
not_entities_file_content = ''

for item in query_result:
	full_text = item['full_text']
	for entity in item['nee_entities']:
		'''
		First I remove the punctuation at the start and the end of the string
		as some of the entities have this error, also I do a trim.
		'''
		dirty_text = entity['text']
		clean_text = dirty_text.strip().lstrip(punctuation).rstrip(punctuation)
		entities_file_content = entities_file_content + clean_text + '\t' + entity['type'] + '\n'

		'''
		Remove the entities text from the full twiter text and accumulate this in a string.
		'''
		
		full_text = full_text.replace(dirty_text,'')
		not_entities_file_content = not_entities_file_content + full_text + ' '

'''
Add numeric entities to the files
'''
for counter in range(number_entity_generator_limit):
	randon_number = random.randint(1,number_entity_generator_limit)
	number_in_string = num2words(randon_number, lang='es')
	for repetition in range(number_repetition_factor):
		entities_file_content += str(randon_number) + '\t' + number_entity + '\n'
		if number_in_string:
			entities_file_content += number_in_string + '\t' + number_entity + '\n'

'''
Add money entities to the files
'''
for counter in range(money_entity_generator_limit):
	randon_number = random.randint(1,money_entity_generator_max)

	for multiple in money_multiples:
		money_number = randon_number * multiple
		number_in_string = num2words(randon_number * multiple, lang='es')

		for symbol in currency_symbols:
			entities_file_content += symbol + str(money_number) + '\t' + money_entity + '\n'
		for suf_pre in currency_suffix_prefix:
			entities_file_content += suf_pre + number_in_string + '\t' + money_entity + '\n'
		for suf in currency_suffix:
			entities_file_content += number_in_string + suf + '\t' + money_entity + '\n'

'''
Now I save the entities in a tsv file
'''
with open ('entities.tsv','w') as entities_file:
	entities_file.write(entities_file_content.encode('utf8'))

'''
Now the full text whitout entities is being saved in another file, the content of this file
must be tokenized using instructions from https://nlp.stanford.edu/software/crf-faq.shtml#a
once tokinzed and annotated with O, the two files from this script must be merged.
'''

with open ('not_entities.txt','w') as not_entities_file:
	not_entities_file.write(not_entities_file_content.encode('utf8'))

# Generating the tokenized file
os.system('java -cp stanford-ner-2018-10-16/stanford-ner.jar edu.stanford.nlp.process.PTBTokenizer not_entities.txt > not_entities.tok')
# Generating the annotated file
os.system('perl -ne \'chomp; print "$_\tO\n"\' not_entities.tok > not_entities.tsv')

#Chop the not_entities.tsv file leaving a sample
not_entities_tokenized_length = int(subprocess.check_output('wc -l < not_entities.tsv', shell=True))

numbers_of_line_to_mantain = int(not_entities_tokenized_length * not_entities_percent_length)
os.system('gshuf -n' + str(numbers_of_line_to_mantain) +' not_entities.tsv > choped_not_entities.tsv')

# Merge the two files
os.system('paste -d \'\n\' entities.tsv choped_not_entities.tsv > output_double_break_lines.txt')

#Randomly generate training and test data files

training_content = ''
test_content = ''

with open('output_double_break_lines.txt','r') as input_file:
	for line in input_file:
		if line.strip():
			if random.uniform(0,1) < training_percent:
				training_content += line
			else:
				test_content += line

with open('training.tsv','w') as training_file:
	training_file.write(training_content)

with open('test.tsv','w') as test_file:
	test_file.write(test_content)


# Remove working files
os.system('rm entities.tsv not_entities.tsv choped_not_entities.tsv not_entities.tok not_entities.txt output_double_break_lines.txt')

