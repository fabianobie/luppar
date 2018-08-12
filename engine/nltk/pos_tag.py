#-*- coding: utf8 -*-

import pickle
import nltk
import os



class PosTagger(object):
    def __init__(self):
        script_dir = os.path.dirname(__file__)
        self.__tag_model = os.path.join(script_dir, "tagger.pkl")
        self.__tagger = pickle.load(open(self.__tag_model, 'rb'))

    def pos_tagger_portuguese(self,sentences):
        try:
            tags = [self.__tagger.tag(nltk.word_tokenize(sentence))[0] for sentence in sentences if len(sentence)>0]
        except:
            print('Erro')
        return tags

    def pos_tagger_english(self,sentences):
        return nltk.pos_tag(sentences, lang='en')



