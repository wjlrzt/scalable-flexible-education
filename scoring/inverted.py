from math import sqrt
import urllib


class Inverted():
	def __init__(self):
		opener = urllib.URLopener()
		myurl = "https://s3-us-west-2.amazonaws.com/pc-api-builder-files/inverted.txt"
		f = opener.open(myurl)

		contents = f.readlines()
		self.wordDict = {}

		for line in contents:
			tokens = line.split()
			word = tokens[0]
			idf = tokens[1]
			total_occurences = tokens[2]

			self.wordDict[word] = {}
			self.wordDict[word]['idf'] = float(idf)
			self.wordDict[word]['total_occurences'] = int(total_occurences)
			self.wordDict[word]['docs'] = {}

			tokens = tokens[3:]
			i = 0

			while i < len(tokens):
				doc_id = tokens[i]
				i += 1
				num_occ = tokens[i]
				i += 1
				norm_factor = tokens[i]
				i += 1

				doc_tuple = (int(doc_id), int(num_occ), sqrt(float(norm_factor)))
				self.wordDict[word]['docs'][int(doc_id)] = doc_tuple

		f.close()
		print('ready from INVERTED')