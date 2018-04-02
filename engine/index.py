# -*- coding: utf-8 -*-
import math
import traceback

import numpy as np
import sys

import nltk
from collections import defaultdict

from scipy.sparse.csgraph._min_spanning_tree import csr_matrix
from sklearn.preprocessing.data import normalize



class DocTermItem:
    def __init__(self, uid, tf=0):
        self.uid = uid
        self.tf = tf
        self.pos = []
        self.tid = None

    def __str__(self):
        return str(self.uid) + ":" + str(self.tf)


class DocItem:
    def __init__(self, id, size=0):
        self.id = int(id)
        self.size = size

    def __str__(self):
        return "D"+str(self.id)+":"+str(self.size)


class InvertedIndex:
    """ Inverted index datastructure """

    def __init__(self, preprocessor):
        self.index = {}
        self.documents = {}
        self.feature_names = {}

        self.preprocessor = preprocessor
        self.matrix = None
        self.avg_size = None

        self.__unique_id = 0
        self.__unique_term_id = 0
        self.__comatrix = None


    def lookup(self, word,preprocess=False):
        """
        Lookup a word in the index
        """
        words = []
        word = word.lower()
        if preprocess:
            words = self.preprocessor.tokenize(word)
        else:
            words.append(word)
        if(words):
            docs = []
            for w in words:
                if self.index.get(w):
                    for dt in self.index.get(w):
                        docs.append(dt.uid)

            return docs

    def term_doc_freq(self, qid, did):
        """
        Lookup a word in the index
        """
        term=self.feature_names[qid]
        docs_item = self.index[term]
        for dt in docs_item:
            if dt.uid == did:
                return dt.tf

        return 0

    def add(self, document):
        """
        Add a document string to the index
        """
        for pos, token in enumerate([t.lower() for t in self.preprocessor.tokenize(document.text)]):
            if(token not in self.index.keys()):
                self.index[token] = []

            if self.__unique_id not in [dt.uid for dt in self.index[token]]:
                dt = DocTermItem(self.__unique_id)
                dt.tf = 1
                dt.pos.append(pos)
                dt.tid = self.__unique_term_id
                self.index[token].append(dt)
                if(token not in self.feature_names.values()):
                    self.feature_names[self.__unique_term_id]=token
                    self.__unique_term_id += 1
            else:
                dt = self.index[token][-1]
                dt.pos.append(pos)
                dt.tf += 1

        d = DocItem(document.id, size=document.size)
        self.documents[self.__unique_id] = d
        #print(self.__unique_id)
        self.__unique_id += 1

    def get_doc_item(self,num):
        return self.documents[num]

    def get_feature_id(self,term):
        try:
            return self.index[term][0].tid #self.feature_names.keys()[self.feature_names.values().index(term)]
        except:
            #traceback.print_exc(file=sys.stdout)
            return None

    def avg_docs(self,force=False):
        if not self.avg_size or force:
            self.avg_size = np.sum([d.size for d in self.documents.values()]) / len(self.documents)

        return self.avg_size

    def print_terms(self):
        for k, v in self.feature_names.items():
            print("%d:%s" % (k,v))

    def print_docs(self):
        for k, v in self.documents.items():
            print("D%d:%s" % (k, v))

    def print_index(self):
        for k, v in self.index.items():
            print("%s:" % k)
            for d in v:
                print("        "+str(d))

    def print_matrix(self):
        print(self.matrix.toarray())

    def print_query(self,q):
        print(self.query_tf_idf(q,do_idf=False).toarray())

    def tf(self, tf, base=10, type=1):
        # Logarithmic
        if type == 1:
            return (1 + math.log(tf, base))
        # Binary
        elif type == 2:
            return int(tf > 0)
        # Raw
        elif type == 3:
            return tf

    def idf(self, n, ni, unary=False, smooth=False, proba=False, base=10):
        fsm = int(smooth)
        fpro = int(proba) * ni
        if unary:
            return 1
        else:
            return math.log(fsm + (float(n - fpro) / ni), base)

    def tf_idf(self, do_idf=True, force=False, smooth=False, proba=False, base=10, norm='l2', type_tf=1):
        ''' Converts Index to tf.idf values
            do_idf: if False, convert to tf only
            type_idf: IDF: Default(Inverted Frequency)
                      SIDF: Smooth Inverted Frequency
                      PIDF: Probabilistic Inverted Frequency
        '''
        if self.matrix == None or force:
            N = len(self.documents)
            M = len(self.index)

            matrix = np.zeros((N, M))
            for j, term in self.feature_names.items():
                docs = self.index[term]
                ni = len(docs)
                for doc in docs:
                    i = doc.uid
                    tf = self.tf(doc.tf, base=base, type=type_tf)
                    idf = self.idf(N, ni, unary=not do_idf, smooth=smooth, proba=proba, base=base)
                    matrix[i][j] = tf * idf

            if norm:
                matrix = normalize(matrix, norm=norm, copy=False)

            self.matrix = csr_matrix(matrix)
            #self.comatrix()
        return self.matrix

    def query_tf_idf(self,query, do_idf=True, force=False, smooth=False, proba=False, base=10, norm=None, type_tf=1):
        ''' Converts Index to tf.idf values
            do_idf: if False, convert to tf only
            type_idf: IDF: Default(Inverted Frequency)
                      SIDF: Smooth Inverted Frequency
                      PIDF: Probabilistic Inverted Frequency
        '''
        N = len(self.documents)
        M = len(self.index)

        matrix = np.zeros((1, M))

        if len(query.query_vector)==0:
            raise "Not query preprocessor"
        if(len(query.query_score)==0):
            terms = nltk.FreqDist(query.query_vector)
            do_idf = True
            type_tf = 1
        else:
            do_idf = False
            type_tf = 3
            terms = dict(zip(query.query_vector, query.query_score))
            norm='l2'

        print(dict(terms))
        for (term, tf) in terms.items():

            j = self.get_feature_id(term)
            if(j):
                ni = len(self.index[term])
                tf = self.tf(tf, base=base, type=type_tf)
                idf = self.idf(N, ni, unary=not do_idf, smooth=smooth, proba=proba, base=base)
                matrix[0][j] = tf * idf
            # else:
            #     print(term)
            #     matrix[0][j] = 0

        if norm:
            matrix = normalize(matrix, norm=norm, copy=False)

        matrix = csr_matrix(matrix)
        return matrix

    @property
    def comatrix(self):
        assert(self.matrix,"Need to calculate matrix")
        if self.__comatrix == None:
            self.__comatrix = self.matrix.T*self.matrix
        return self.__comatrix