# coding: utf-8
# ners.py
# Adapted from guide found here: https://www.depends-on-the-definition.com/introduction-named-entity-recognition-python/


# imports

import pandas as pd
import numpy as np
# import sklearn
from sklearn_crfsuite import CRF
# from sklearn.cross_validation import cross_val_predict
# from sklearn_crfsuite.metrics import flat_classification_report
# import eli5
import nltk
import pickle

############################################################################################################
# Building Model for Named Entity Recognition

# loading dataset
# training_data= pd.read_csv("data/ner_dataset.csv", encoding="latin1")
# training_data = training_data.fillna(method="ffill")

# # Peek at the data
# training_data.tail(10)

############################################################################################################
# Function Call Format
def createNamedEntities(raw_text):
    crf = pickle.load(open('final_crf.sav', 'rb'))
    unprocessed_text = raw_text

    # split raw text into list of sentences
    raw_sentences = []
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    raw_sentences = tokenizer.tokenize(unprocessed_text)

    # list of tagged sentences
    tagged_sentences = []
    for sentence in raw_sentences:
        text = nltk.word_tokenize(sentence)
        tagged = nltk.pos_tag(text)
        tagged_sentences.append(tagged)

    # Convert tagged raw text to features
    raw_text_features = [convertToFeatures(sentence) for sentence in tagged_sentences]
    # Make predictions using feature vectors
    preds = crf.predict(raw_text_features)

    ####################################################################################
    # Group sequential named entitites together
    last_index = 0
    combined_named_entities = []
    for i, sentence in enumerate(tagged_sentences):
        j = 0 
        while j < len(sentence):
        # for j, word in enumerate(sentence):
            combined_indices = [j]
            if preds[i][j] != 'O':
                
                while preds[i][j+1] != 'O':
                    j+= 1
                    combined_indices.append(j)
                    # last_index = c

                w = ''
                for num in combined_indices:
                    w += sentence[num][0] + ' '
                combined_named_entities.append(w)
            j+=1

    return list(set(combined_named_entities))
    
    with open('text_files/combined_named_entities.txt', 'w') as f:
        for entity in combined_named_entities:
            f.write(entity +'\n')




# class for retrieving a sentence
# will create a tuple of word, pos, and tag
class RetrieveSentence(object):
    
    def __init__(self, data):
        self.sentence_num = 1
        self.data = data
        self.is_empty = False
        # Aggregating data
        agg_func = lambda s: [(w, p, t) for w, p, t in zip(s["Word"].values.tolist(),
                                                           s["POS"].values.tolist(),
                                                           s["Tag"].values.tolist())]
        self.grouped = self.data.groupby("Sentence #").apply(agg_func)
        self.all_sentences = [s for s in self.grouped]
    
    def get_next(self):
        try:
            s = self.grouped["Sentence: {}".format(self.sentence_num)]
            self.sentence_num += 1
            return s
        except:
            return None


# retrieval = RetrieveSentence(training_data)
# # sentence = retrieval.get_next()

# # sentence contrains a list of tuples, each tuple is the word, pos, and tag

# # retrieve all of the sentences as tuple
# all_sentences = retrieval.all_sentences


# Feature Engineering
# Feature Engineering Strategy defined by Tobias Sterbak (https://www.depends-on-the-definition.com/about/)
def wordToFeature(sentence, i):
    word = sentence[i][0]
    postag = sentence[i][1]

    features = {
        'bias': 1.0,
        'word.lower()': word.lower(),
        'word[-3:]': word[-3:],
        'word[-2:]': word[-2:],
        'word.isupper()': word.isupper(),
        'word.istitle()': word.istitle(),
        'word.isdigit()': word.isdigit(),
        'postag': postag,
        'postag[:2]': postag[:2],
    }
    if i > 0:
        word1 = sentence[i-1][0]
        postag1 = sentence[i-1][1]
        features.update({
            '-1:word.lower()': word1.lower(),
            '-1:word.istitle()': word1.istitle(),
            '-1:word.isupper()': word1.isupper(),
            '-1:postag': postag1,
            '-1:postag[:2]': postag1[:2],
        })
    else:
        features['BOS'] = True

    if i < len(sentence)-1:
        word1 = sentence[i+1][0]
        postag1 = sentence[i+1][1]
        features.update({
            '+1:word.lower()': word1.lower(),
            '+1:word.istitle()': word1.istitle(),
            '+1:word.isupper()': word1.isupper(),
            '+1:postag': postag1,
            '+1:postag[:2]': postag1[:2],
        })
    else:
        features['EOS'] = True

    return features


def convertToFeatures(sentence):
    return [wordToFeature(sentence, i) for i in range(len(sentence))]

def convertToLabels(sentence):
    return [label for token, postag, label in sentence]

def convertToTokens(sentence):
    return [token for token, postag, label in sentence]


def main():
    features_vec = [convertToFeatures(sentence) for sentence in all_sentences]
    labels = [convertToLabels(sentence) for sentence in all_sentences]


    # instantiate CRF object
    # L1 regularization parameter increased to improve focus on context
    crf = CRF(algorithm='lbfgs',
              c1=100,
              c2=0.1,
              max_iterations=100,
              all_possible_transitions=False)

    print ("Model Built.")

    # # Make prediction on data with 5-folds cross validation
    # predictions = cross_val_predict(estimator=crf, X=features_vec, y=labels, cv=5)
    # print ("5 Folds Cross Validation Complete")

    # # 5-folds cross validation report
    # cv_report = flat_classification_report(y_pred=predictions, y_true=labels)
    # print(cv_report)

    # train model
    crf.fit(features_vec, labels)
    pickle.dump(crf, open('final_crf.sav', 'wb'), protocol=2)

    print ("Data has been fit to features")

    # # Look at the weights
    # eli5.show_weights(crf, top=30)


    # Read raw text
    unprocessed_text = ''
    with open("text_files/rawtext.txt", "r") as raw:
        unprocessed_text = raw.read()

    # split raw text into list of sentences
    raw_sentences = []
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    raw_sentences = tokenizer.tokenize(unprocessed_text)

    # list of tagged sentences
    tagged_sentences = []
    for sentence in raw_sentences:
        text = nltk.word_tokenize(sentence)
        tagged = nltk.pos_tag(text)
        tagged_sentences.append(tagged)

    # Convert tagged raw text to features
    raw_text_features = [convertToFeatures(sentence) for sentence in tagged_sentences]
    # Make predictions using feature vectors
    preds = crf.predict(raw_text_features)

    ####################################################################################
    # Sequential named entitites are not grouped

    # outputting
    named_entities = []
    tagged_named_entities = []
    for i, sentence in enumerate(tagged_sentences):
        for j, word in enumerate(sentence):
            # if the word in the sentence is a named entity:
            if preds[i][j] != 'O':
                # print(word[0])
                named_entities.append(word[0])
                tmp = (word[0], preds[i][j])
                tagged_named_entities.append(tmp)

    with open('text_files/named_entities.txt', 'w') as f:
        for entity in named_entities:
            f.write(entity +'\n')

    with open('text_files/tagged_named_entities.txt', 'w') as f:
        for entity in tagged_named_entities:
            f.write(entity[0] + ': ' + entity[1]  +'\n')



    ####################################################################################
    # Group sequential named entitites together
    last_index = 0
    combined_named_entities = []
    for i, sentence in enumerate(tagged_sentences):
        j = 0 
        while j < len(sentence):
        # for j, word in enumerate(sentence):
            combined_indices = [j]
            if preds[i][j] != 'O':
                
                while preds[i][j+1] != 'O':
                    j+= 1
                    combined_indices.append(j)
                    # last_index = c

                w = ''
                for num in combined_indices:
                    w += sentence[num][0] + ' '
                combined_named_entities.append(w)
            j+=1

    with open('text_files/combined_named_entities.txt', 'w') as f:
        for entity in combined_named_entities:
            f.write(entity +'\n')

if __name__ == '__main__':
    main()



