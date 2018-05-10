#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, request
import json
import requests
from bs4 import BeautifulSoup
import re
from operator import itemgetter
from math import sqrt, log, ceil
from string import punctuation

from scoring.stopwords_initializer import Stopwords
from scoring.inverted import Inverted
from ners import createNamedEntities

from nltk.stem import WordNetLemmatizer
# from aylienapiclient import textapi

# from keys import ALYIEN_APP_ID, ALYIEN_KEY

application = Flask(__name__)
application.debug = True

stopwords = Stopwords()
inverted = Inverted()
lemmatizer = WordNetLemmatizer()
print("Ready from all three systems.")

# TODO: Dynamically change this as environment variable
# or, have feature in indexing API to get this number
num_CORPUS_DOCUMENTS = 5000


# API Usage:
# URL = #TODO
# GET Request:
# Input: Nothing
# Output: Nothing
# POST Request:
# Input = JSON Formatted with two inputs -
# 1. 'documents' (list) - list of inputs, either text or links
# 2. 'num_keywords' (integer) - number of keywords user wants returned
# Output = JSON Formatted response with 2 lists ('words', 'point_values'), 'total_points' (int) , and 'error_message' (string)


def tokenize_ne(named_entities):
    tokenized_ne = dict()
    for ne in named_entities:
        for ne_token in ne.split():
            tokenized_ne[ne_token.lower()] = ne

    return tokenized_ne


def get_word_ranking(text_final, document_term_frequencies, num_docs, named_entities):
    word_ranking = []
    named_entities_tokenized = tokenize_ne(named_entities)

    for word in set(text_final):
        word_stats = inverted.wordDict.get(word)

        if word_stats == None:
            # IDF = log(Total Documents in Corpus / 1 + 1)
            idf = log(num_CORPUS_DOCUMENTS / 2)

        else:
            idf = word_stats['idf']

        norm_factor = 0.0
        tf = 0.0

        for document_number in range(0, num_docs):
            if document_term_frequencies[document_number].get(word) == None:
                continue
            # found the word in this document
            else:
                norm_factor += sqrt(float(len(document_term_frequencies[document_number])))
                tf += document_term_frequencies[document_number].get(word)

        ne_multiplier = 1.0
        new_word = word
        if word in named_entities_tokenized:
            new_word = named_entities_tokenized[word]
            ne_multiplier = 2.0

        word_ranking.append((new_word, float(tf * idf * ne_multiplier) / float(norm_factor)))

    return word_ranking

def process_text(full_documents):
    text_final = []
    text_raw_list = []

    document_term_frequencies = []
    # checking if it is a link or plain text
    for document_number, d in enumerate(full_documents):
        document_term_frequencies.append({})

        text_raw = ""
        is_link = False
        h1_words = ""

        # it is a link
        if d.find(' ') == -1:
            r = requests.get(d).text
            soup = BeautifulSoup(r, 'html.parser')
            text_p = soup.find_all('p', text=True)
            for item in text_p:
                text_raw = text_raw + item.string + " "

            text_h1 = soup.find_all('h1', text=True)
            title_words = soup.title

            for item in text_h1:
                h1_words = h1_words + item.string + " "

            for item in title_words:
                h1_words = h1_words + item + " "

            is_link = True

        # body of text
        else:
            text_raw = d

        # clean, format the body of text
        text_raw = text_raw.replace('-', ' ')
        text_raw = text_raw.replace('\n', '  ')
        text_raw = text_raw.replace('...', '  ')
        text_raw = text_raw.replace('  ', '  ').encode('ascii', 'ignore')

        h1_word_list = []

        if is_link:
            # clean, format the title
            h1_words = h1_words.replace('-', ' ')
            h1_words = h1_words.replace('\n', '  ')
            h1_words = h1_words.replace('...', '  ')
            h1_words = h1_words.replace('  ', '  ').encode('ascii', 'ignore')
            h1_word_list = h1_words.split()
            # TODO: S3
            h1_word_list = [lemmatizer.lemmatize(item.lower()) for item in h1_word_list]

        # tokenize the text
        words = text_raw.split()
        text_raw_list.append(text_raw)

        # remove special characters and stop words
        for idx, word in enumerate(words):
            word = str(words[idx])
            is_proper = False

            # boost if it is a proper
            if word[0].isupper():
                is_proper = True

                # is it just a capitalized because it is the first word in sentence
                # Comment Justification: First words are often most import nouns in sentence
                # if idx == 0 or words[idx - 1][-1:] in punctuation:
                #     is_proper = False

            word = word.lower()

            word = re.sub(r'[^a-zA-Z0-9]+', '', str(word))

            # only numbers that are allowed are four digit (years)
            if bool(re.search(r'\d+', word)):
                word = re.search(r'\d+', word).group()

                if len(word) != 4:
                    continue

            if word in stopwords.stopwordDict or word == '':
                continue

            # lemmatizing code
            if not is_proper:
                # TODO: s3
                word = lemmatizer.lemmatize(word)
                # print(word)

            # add to a text_final document

            # Weight bodies of text heavier (x1.5 currently)
            if is_link:
                weighted_frequency = 1.0
                if word in h1_word_list:
                    weighted_frequency = 4.0

            else:
                weighted_frequency = 1.5

            # weight proper nouns slightly heavier
            if is_proper:
                weighted_frequency += .25

            if document_term_frequencies[document_number].get(word) == None:
                document_term_frequencies[document_number][word] = weighted_frequency
            else:
                document_term_frequencies[document_number][word] += weighted_frequency

            text_final.append(word)


    return ' '.join(text_raw_list), text_final, document_term_frequencies

def assign_point_values(sorted_words, num_keywords):
    top_words = []
    point_values = []

    i = 0
    total_sum = 0
    while i < num_keywords:
        if sorted_words[i][0] in top_words:
            i += 1
            continue
        top_words.append(sorted_words[i][0])
        total_sum += sorted_words[i][1]
        i += 1

    i = 0
    total_adjusted_point_values = 0
    while i < num_keywords:
        point_val = ceil(100 * float(sorted_words[i][1]) / float(total_sum))
        total_adjusted_point_values += point_val
        point_values.append(point_val)
        i += 1

    return top_words, point_values, total_adjusted_point_values


def demo486(documents, num_keywords):
    num_docs = len(documents)

    # process the documents that come in, get the term frequencies
    text_raw, text_final, document_term_frequencies = process_text(documents)
    # extract the named entities, using the trained model from ners.py
    named_entities = createNamedEntities(text_raw)

    # Return highest N tf-idf scores for the entire document
    word_ranking = get_word_ranking(text_final, document_term_frequencies, num_docs, named_entities)

    # sort the words in descending (high to low) order based on points
    sorted_words = sorted(word_ranking, key=itemgetter(1), reverse=True)

    # normalize the point values to sum up to 100
    top_words, point_values, total_adjusted_point_values = assign_point_values(sorted_words, num_keywords)

    return top_words, point_values, named_entities


@application.route('/', methods=['GET', 'POST'])
@application.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return json.dumps({
            'error_message' : 'You have reached this page in error.'
            })
    else:
        pass # Readability, POST request

    full_json = request.get_json()
    full_documents = full_json['documents']
    num_primary_keywords = full_json['num_primary_keywords']
    num_keywords = num_primary_keywords + full_json['num_secondary_keywords']

    num_docs = len(full_documents)

    text_raw, text_final, document_term_frequencies = process_text(full_documents)
    named_entities = createNamedEntities(text_raw)

    # Return highest N tf-idf scores for the entire document
    word_ranking = get_word_ranking(text_final, document_term_frequencies, num_docs, named_entities)

    # alyien_concepts = get_alien_concepts(full_documents)

    sorted_words = sorted(word_ranking, key=itemgetter(1), reverse=True)

    top_words, point_values, total_adjusted_point_values = assign_point_values(sorted_words, num_keywords)

    print(json.dumps({
        'primary_words':top_words[0:num_primary_keywords],
        'primary_point_values': point_values[0:num_primary_keywords],
        'named_entities': named_entities,
        'secondary_words' : top_words[num_primary_keywords+1:],
        'secondary_point_values' : point_values[num_primary_keywords+1:],
        'total_points':total_adjusted_point_values,
        'error_message':None,
        'raw_text':text_raw
        }))

    return json.dumps({
        'primary_words':top_words[0:num_primary_keywords],
        'primary_point_values': point_values[0:num_primary_keywords],
        'named_entities': named_entities,
        'secondary_words' : top_words[num_primary_keywords:],
        'secondary_point_values' : point_values[num_primary_keywords:],
        'total_points':total_adjusted_point_values,
        'error_message':None,
        'raw_text':text_raw
        })

if __name__ == '__main__':
    application.run(host='0.0.0.0')
