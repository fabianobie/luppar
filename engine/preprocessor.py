# -*- coding: utf-8 -*-

import nltk
import re
import unicodedata

from nltk.corpus import stopwords
from os.path import isfile
from engine.index import InvertedIndex
from engine.util import save_object, load_object


class Preprocessor(object):

    def __init__(self,source,use_stop_words=False,stemming=None,pos_tag=False,numbers=False,file_path="../data/",lang='en', save=True):
        self.source = source
        self.stemming = stemming
        self.file_path = file_path
        self.numbers = numbers
        self.__use_stop_words = use_stop_words
        self.pos_tag = pos_tag
        self.lang = lang

        self.representation = None
        self.querys = None
        self.__index_file = '/tmp/index%s.idx'
        self.__querys_file = '/tmp/querys%s.idx'
        self.__stemming_list = None
        self.save = save

        if self.__use_stop_words:
            self.stop_words = self.get_stop_words()

    def get_representation_docs(self, force=False, do_matrix=True,do_idf=True,norm='l1',type_tf=1):
        if(not self.representation):
            if not force:
                if isfile(self.__index_file % (self.source.info)):
                    self.representation=load_object(self.__index_file % (self.source.info))
                else:
                    force=True

            if force:
                self.representation = InvertedIndex(self)
                for doc in self.source.read_docs():
                    if self.save:print(doc.id)
                    self.representation.add(doc)
                if do_matrix:
                    self.representation.tf_idf(do_idf=do_idf,norm=norm,type_tf=type_tf)
                if self.save:
                    save_object(self.representation, self.__index_file%(self.source.info))

        return self.representation

    def get_representation_query(self,force=False):
        if (not self.querys):
            if not force:
                if isfile(self.__querys_file % (self.source.info)):
                    self.querys = load_object(self.__querys_file % (self.source.info))
                else:
                    force = True

            if force:
                self.querys = []
                for q in self.source.read_querys():
                    self.querys.append(q)
                if self.save:
                    save_object(self.querys, self.__querys_file % (self.source.info))

        return self.querys

    def tokenize(self, text=''):
        text = self.remove_accents(text)
        terms = [word for sent in nltk.sent_tokenize(text)
                 for word in nltk.word_tokenize(self.clear_text(sent))
                 if not self.use_stop_words or word not in self.stop_words]


        terms = self.reduction(terms)

        if self.pos_tag:
            terms = nltk.pos_tag(terms)

        if self.stemming:
            if not self.pos_tag:
                stems = [self.stem(t) for t in terms]
            else:
                stems = [(self.stem(tr),tg) for (tr,tg) in terms]
            return stems
        return terms

    def stem(self, term):

        if self.stemming:
            stemmer = self.get_stemming(self.stemming)
            term = stemmer.stem(term).lower()
        return term

    def ngram_tokenize(self, text=''):
        n = self.ngram
        terms = self.tokenize(text=text)
        if n == 1:
            return terms
        n_grams = []
        for i in range(0, len(terms) - n + 1):
            n_grams.append(" ".join(terms[i:i + n]))
        return n_grams

    def get_stop_words(self):
        if self.lang=='en':
            stop_words = set(stopwords.words(self.stemming))
        elif self.lang=='pt-br':
            stop_words = set(stopwords.words('portuguese')).union(stopwords.words('english'))
        return stop_words

    def get_stemming(self,type):
        if not self.__stemming_list:
                self.__stemming_list = {'rslps': nltk.stem.RSLPStemmer(), 'porter': nltk.PorterStemmer(),
                                         'lancaster': nltk.LancasterStemmer(),
                                         'english': nltk.stem.snowball.EnglishStemmer(),
                                         'portuguese': nltk.stem.snowball.PortugueseStemmer()}
        return self.__stemming_list[type]

    def clear_text(self, text=''):
        #If Numbers
        nb = '0-9' if self.numbers else ''
        #Clear text
        text = text.replace(u'-\n', '').replace(u'-\r\n', '')
        text = re.sub(u'[^a-zA-ZáéíóúÁÉÍÓÚâêîôÂÊÎÔãõÃÕçÇ'+nb+' ]', ' ', text).strip().lower()

        return text

    def remove_accents(self,data):
        if not isinstance(data, str):
            data = str(data, "utf-8")
        return ''.join((c for c in unicodedata.normalize('NFD', data) if unicodedata.category(c) != 'Mn'))

    def reduction(self,terms):
        return terms

    @property
    def use_stop_words(self):
        return self.__use_stop_words

    @use_stop_words.setter
    def use_stop_words(self,value):
        self.__use_stop_words = value
        if self.__use_stop_words:
            self.stop_words = self.get_stop_words()



class GenericPreprocessor(Preprocessor):

    def __init__(self,source):
        source = source
        super(GenericPreprocessor,self).__init__(source=source,stemming='english',file_path="../data/")


class EnglishPreprocessor(Preprocessor):

    def __init__(self,source,use_stop_words=False):
        source = source
        super(EnglishPreprocessor,self).__init__(source=source,stemming='english',file_path="../data/",use_stop_words=use_stop_words)


class PortuguesePreprocessor(Preprocessor):

    def __init__(self,source,use_stop_words=False):
        source = source
        super(PortuguesePreprocessor,self).__init__(source=source,stemming='rslps',file_path="../data/",use_stop_words=use_stop_words,lang='pt-br')

    def reduction(self,terms):
        return [t for t in terms if len(t)>2]



if __name__ == '__main__':
    pre = Preprocessor(source=None,use_stop_words=True)
    texto = '''

    what similarity laws must be obeyed when constructing aeroelastic models
of heated high speed aircraft .
    '''
    res = pre.tokenize(text=texto)
    print(res)
