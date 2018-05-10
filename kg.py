# kg.py
# Given a list of missed topics, this program will return related topics as indicated by 
#	the google knowledge graph

import json
import urllib

# strip new line characters

def get_kg_topics(queries, prefix):
	queries = [x.strip() for x in queries] 

	# API Info
	api_key = open('.apikey').read()
	service_url = 'https://kgsearch.googleapis.com/v1/entities:search'

	related_items = []

	# Collect knowledge graph responses for topics
	for query in queries:
		params = {
		    'query': query,
		    'limit': 5,
		    'indent': True,
		    'key': api_key,
		}
		url = service_url + '?' + urllib.urlencode(params)
		response = json.loads(urllib.urlopen(url).read())
		related_items.append(response)

	# Output related topics to file
	output = ''
	extra_seeds = []

	for i, response in enumerate(related_items):
		output += 'More information for ' + queries[i] + ' can be found by researching:\n'
		output += '--------------------\n'
		
		for element in response['itemListElement']:
			output +=  (element['result']['name']).encode('utf-8') + ' (' + str(element['resultScore']) + ')\n'
			try: extra_seeds.append((element['result']['detailedDescription']['url']))
			except: pass
			
		output += '\n'

	with open('text_files/{}_suggested_topics.txt'.format(prefix), 'w') as f:
		f.write(output)


	with open('text_files/{}_additional_links.txt'.format(prefix), 'w') as f:
		for seed in extra_seeds:
			f.write(seed)
			f.write('\n')


if __name__ == '__main__':
	# Read in missed topics from file
	queries = []
	with open('text_files/missed.txt', 'r') as f:
		queries = f.readlines()

	queries = [x.strip() for x in queries] 

	# API Info
	api_key = open('.apikey').read()
	service_url = 'https://kgsearch.googleapis.com/v1/entities:search'

	related_items = []

	# Collect knowledge graph responses for topics
	for query in queries:
		params = {
		    'query': query,
		    'limit': 5,
		    'indent': True,
		    'key': api_key,
		}
		url = service_url + '?' + urllib.urlencode(params)
		response = json.loads(urllib.urlopen(url).read())
		related_items.append(response)

	# Output related topics to file
	output = ''
	extra_seeds = []
	for i, response in enumerate(related_items):
		output += 'More information for ' + queries[i] + ' can be found by researching:\n'
		output += '--------------------\n'
		for element in response['itemListElement']:
			output +=  (element['result']['name']).encode('utf-8') + ' (' + str(element['resultScore']) + ')\n'
			try: extra_seeds.append((element['result']['detailedDescription']['url']))
			except: pass
			
		output += '\n'

	with open('text_files/suggested_topics.txt', 'w') as f:
		f.write(output)


	with open('text_files/additional_links.txt', 'w') as f:
		for seed in extra_seeds:
			f.write(seed)
			f.write('\n')
	# get_kg_topics(queries)
