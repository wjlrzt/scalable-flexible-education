import urllib

class Stopwords():
	def __init__(self):
		opener = urllib.URLopener()
		myurl = "https://s3-us-west-2.amazonaws.com/pc-api-builder-files/stopwords.txt"
		f = opener.open(myurl)

		contents = f.readlines()

		self.stopwordDict = {}

		for sw in contents:
			sw = sw.rstrip('\n')
			self.stopwordDict[sw] = True

		f.close()

		print('ready from STOPWORDS')