# A Scalable, Flexible Augmentation of the Student Education Process

Please see [our paper](https://arxiv.org/abs/1810.09845) for more details, which will appear at the [NIPS 2018 AI for Social Good Workshop](https://aiforsocialgood.github.io/2018/cfp.htm).

### Dataset used to train NERS Model:
- Corpus features a tagged portiong from the Groningen Meaning Bank tagged specifically for training a model for named entity extraction.
- [Entity Annotated Corpus](https://www.kaggle.com/abhinavwalia95/entity-annotated-corpus)
- [Groningen Meaning Bank](http://gmb.let.rug.nl/data.php)
- Directions:
	- Download data from kaggle, unzip and store both csvs in a data folder.

### Types of Named Entities:
1) geo = Geographical Entity
2) org = Organization
3) per = Person
4) gpe = Geopolitical Entity
5) tim = Time indicator
6) art = Artifact
7) eve = Event
8) nat = Natural Phenomenon
9) o = Other (Considered to be NOT a named entity

### Dependencies
- Numpy
- Pandas
- Sklearn
- Sklearn-CRF
- eli5
- nltk
- json
- urllib

### Running Files
1) ners.py generates two text files of named entities
	- File must be run using Python3
	- Currently uses text_files/raw_text.txt as source for raw text
	- Outputs to text_files/named_entities.txt and text_files/tagged_named_entities.txt 

2) kg.py queries the knowledge graph to find relationally relevant topics based on a seed list of missed topics
	- File must be run using Python2
	- Currently uses text_files/missed.txt as seed list
	- Outputs to text_files/suggested_topics.txt 
	- Requires an api key from Google for the Knowledge Graph API
	- Store API Key in local file called '.apikey' in main directory. This file is included in gitignore
	
Inside of `scoring/`, you will find a few files related to how we score. We use an inverted index, created and uploaded to Amazon S3 (see `inverted.py`) and a stop words class (located in `stopwords.py`). Our main function in `scoring/application.py` can be found on Line 233, `demo486.py`, where we walk through what each function in the file does.

To run a demo, you can run `486demo.py` in the root directory. A sample use case follows:

```
> Welcome, please type your question.
Who was George Washington
> Please give the name of the source document
gw # Note, gw is the file with the source document, see gw.txt
> How many key topics would you like extracted?
5
... Output from the program ...
> Now, the demo will switch to student mode...
> Who was George Washington
> Please type in your answer now
George Washington was a general in the Revolutionary War who fought against the British.

```
