import pymongo
import os
import random

remote_mongo_url = 'mongodb://negra:jamaicanGirl@ec2-34-212-201-251.us-west-2.compute.amazonaws.com/nee_experiment'
client = pymongo.MongoClient(remote_mongo_url)
db = client.nee_experiment

query_result = db.tweets.find( {'$and':[{'nee_entities':{'$exists':True}}]},{'_id':0,'full_text':1,'nee_entities':1})

punctuation = '!"#$%&\'()*+,-./:;<=>?[\\]^_`{|}~'

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

# Merge the two files
os.system('paste -d \'\n\' entities.tsv not_entities.tsv > output_double_break_lines.txt')

#Randomly generate training and test data files

training_content = ''
test_content = ''

with open('output_double_break_lines.txt','r') as input_file:
	for line in input_file:
		if line.strip():
			if random.uniform(0,1) < 0.7:
				training_content += line
			else:
				test_content += line

with open('training.tsv','w') as training_file:
	training_file.write(training_content)

with open('test.tsv','w') as test_file:
	test_file.write(test_content)


# Remove working files
os.system('rm entities.tsv not_entities.tok not_entities.txt not_entities.tsv output_double_break_lines.txt')
