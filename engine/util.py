# -*- coding: utf-8 -*-

import nltk
import re
import unicodedata
import numpy as np
import pickle
import scipy
import sys
import os
import platform

from os import listdir
from os.path import isfile, join

import importlib
from unidecode import unidecode
from nltk.corpus import stopwords
from nltk.stem.snowball import PortugueseStemmer
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
from nltk.corpus import wordnet as wn

from scipy.sparse import csr_matrix



class RepresentWords:
    def __init__(self,documents,tfidf):
        self.tfidf = tfidf
        self.vector_tfidf = tfidf.fit_transform(documents)
        tfidf.use_idf = False
        tfidf.norm = None
        self.count_tf = tfidf.fit_transform(documents)
        self.matrix_tfidf = self.vector_tfidf
        self.matrix_binary = csr_matrix(scipy.sign(self.count_tf.toarray()))

        #self.XT = self.matrix_binary.T * self.matrix_binary
        #self.XD = self.matrix_binary * self.matrix_binary.T

        self.KT = np.dot(self.matrix_tfidf.T, self.matrix_tfidf)
        #self.KD = self.matrix_tfidf * self.matrix_tfidf.T

        self.terms = self.tfidf.get_feature_names()


    def sort_matrix(self, m, n):
        # Converte para Matrix
        mtx = m
        #     print(list(range(len(mtx[0,:]))))
        #     print(mtx[0,:])

        # Converte matrix espaca em array para ordenar por TFIDF
        s = [np.sum(x) for x in mtx.T]
        sorted_s = sorted(s)
        sorted_s = np.array(sorted_s)

        s_id_sorted = sorted(range(len(s)), key=lambda k: s[k], reverse=True)[:n]

        # print(s_id_sorted)
        return mtx.T[s_id_sorted].T, s_id_sorted

    def sort_reduce_tfidf(self, n):

        # Converte para Matrix
        mtx = self.vector_tfidf.toarray()

        # Converte matrix espaca em array para ordenar por TFIDF
        s = [np.sum(x) for x in mtx.T]
        sorted_s = sorted(s)
        sorted_s = np.array(sorted_s)
        if (not n): n = len(s)

        s_id_sorted = sorted(range(len(s)), key=lambda k: s[k], reverse=True)[:n]

        # print(s_id_sorted)
        self.matrix_tfidf = mtx.T[s_id_sorted].T
        self.matrix_binary = scipy.sign(self.matrix_tfidf)
        self.terms = np.array(self.tfidf.get_feature_names())[s_id_sorted]
        return

    def row_sparces(self,indptr):
        a = []
        for m in range(len(indptr)):
            if (m < len(indptr) - 1):
                for i in range(indptr[m], indptr[m + 1]):
                    a.append(m)

        return np.array(a)


class PreProcessWords:

    def __init__(self, prefix = (), sufix = ()):
        self.PREFIX = prefix
        self.SUFIX = sufix

        #importlib.reload(sys)
        #sys.setdefaultencoding('utf8')

        # Conectivos em portugues
        self.STOP_WORDS = set(stopwords.words('portuguese'))
        # Pontuacao
        self.STOP_WORDS.update(['.', ',', '"', "'", '?', '!', ':', ';', '(', ')', '[', ']', '{', '}'])
        fname = "../engine/resources/stop_word.txt"
        with open(fname, "r") as f:
            content = f.readlines()
            for w in content:
                self.STOP_WORDS.add(w.strip())

    def remove_stop_words(self):
        pass

    def clear_unecessary(self,s):
        s = re.sub(u'[^a-zA-ZáéíóúÁÉÍÓÚâêîôÂÊÎÔãõÃÕçÇ \n]', '', s).strip()
        lines = s.splitlines(True)

        sentence = "".join([l for l in lines if (not l.startswith(self.PREFIX) and not l.endswith(self.SUFIX))])
        # print(sentence)

        line = self.join_words(sentence)
        line = re.sub(r'[\w\.-]+@[\w\.-]+', '', sentence)
        line = re.sub(
            r'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))',
            '', line)
        line = re.sub(u'[\'\.]', '', line)
        line = re.sub(r'\w*\d\w*', '', line)
        return line


    def clear_text(self, tokens):
        filtered_tokens = []
        # Apenas palavras sem numeros
        for token in tokens:
            if re.search('[a-zA-Z]', token):
                filtered_tokens.append(token)
        list_of_words = [i.lower() for i in filtered_tokens if i.lower() not in self.STOP_WORDS]

        return list_of_words


    def tokenize(self,text):
        #text = self.join_words(text)
        text = self.remove_accents(text)
        # Split Sentenças e em seguida palavras
        tokens = [unidecode(word) for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(self.clear_unecessary(sent))]

        stemmer = PortugueseStemmer()

        filtered_tokens = self.clear_text(tokens)
        stems = [stemmer.stem(t) for t in filtered_tokens]
        return stems

    def remove_accents(self,data):
        return ''.join((c for c in unicodedata.normalize('NFD', data) if unicodedata.category(c) != 'Mn'))

    def join_words(self,data):
        return data.replace('- ','')

    def convert_pdf_to_txt(self,path):
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
        fp = open(path, 'rb')
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 0
        caching = True
        pagenos=set()

        for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
            interpreter.process_page(page)

        text = retstr.getvalue()

        fp.close()
        device.close()
        retstr.close()

        #u = text.decode('cp1251') # decode from cp1251 byte (str) string to unicode string
        #s = text.encode('utf-8','ignore')  # re-encode unicode string to  utf-8 byte (str) string

        return text

    def convert_pdf_to_txt2(self, path):
        num_doc = path.split("/")[-1].split(".")[0]
        os.system("pdftotext '%s' '%s'" % (path, '/tmp/'+num_doc+'.txt'))
        with open('/tmp/'+num_doc+'.txt', 'r') as f:
            fdocs_read = f.read()

        return fdocs_read



def remover_palavras_chaves(texto):
    parameter = 'flag;(palavras-chave(s)?(?P<palavras_chave>.*?)([1]|abstract|introd))'
    p = texto
    method, regex = parameter.split(';', 1)

    if method == 'flag':
        reobj = re.compile(regex, re.DOTALL)
    else:
        reobj = re.compile(regex)

    result = []
    for m in reobj.finditer(str.lower(p)):
        for n, v in m.groupdict().items():
            if v:
                v = v.replace(u';', ',')
                v = v.replace(u'[^a-zA-ZáéíóúÁÉÍÓÚâêîôÂÊÎÔãõÃÕçÇ;:., ]', '').strip()
                v = v.replace(u'-\n', '')

                key_word = re.compile(re.escape(v), re.IGNORECASE)
                texto = key_word.sub('',texto)
                result.append(v)
        #break

    if len(result)>0:
        result.sort(key=len, reverse=False)
        return texto, result[0]
    return texto,[]

def read_files_from(path,extension):
    return [join(path, f) for f in listdir(path) if isfile(join(path, f)) and '.'+extension in f]



class MacOSFile(object):

    def __init__(self, f):
        self.f = f

    def __getattr__(self, item):
        return getattr(self.f, item)

    def read(self, n):
        # print("reading total_bytes=%s" % n, flush=True)
        if n >= (1 << 31):
            buffer = bytearray(n)
            idx = 0
            while idx < n:
                batch_size = min(n - idx, 1 << 31 - 1)
                # print("reading bytes [%s,%s)..." % (idx, idx + batch_size), end="", flush=True)
                buffer[idx:idx + batch_size] = self.f.read(batch_size)
                # print("done.", flush=True)
                idx += batch_size
            return buffer
        return self.f.read(n)

    def write(self, buffer):
        n = len(buffer)
        print("writing total_bytes=%s..." % n, flush=True)
        idx = 0
        while idx < n:
            batch_size = min(n - idx, 1 << 31 - 1)
            print("writing bytes [%s, %s)... " % (idx, idx + batch_size), end="", flush=True)
            self.f.write(buffer[idx:idx + batch_size])
            print("done.", flush=True)
            idx += batch_size


def save_object(obj, filename):
    with open(filename, 'wb') as output:
        if 'Darwin' in platform.system():
            pickle.dump(obj, MacOSFile(output), pickle.HIGHEST_PROTOCOL)
        else:
            pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)

def load_object(filename):
    with open(filename, 'rb') as input:
        if 'Darwin' in platform.system():
            return pickle.load(MacOSFile(input))
        else:
            return pickle.load(input)

def get_class(kls):
    if kls:
        parts = kls.split('.')
        module = ".".join(parts[:-1])
        m = __import__(module)
        for comp in parts[1:]:
            m = getattr(m, comp)
        return m


def synonymous(word, pos=None):
    list_syn = wn.synsets(word, pos)
    for i, syn in enumerate(list_syn):
        syns = [n.replace('_', ' ') for n in syn.lemma_names()]
        return syns[:2]


from collections import OrderedDict, Callable

class DefaultOrderedDict(OrderedDict):
    # Source: http://stackoverflow.com/a/6190500/562769
    def __init__(self, default_factory=None, *a, **kw):
        if (default_factory is not None and
                not isinstance(default_factory, Callable)):
            raise TypeError('first argument must be callable')
        OrderedDict.__init__(self, *a, **kw)
        self.default_factory = default_factory

    def __getitem__(self, key):
        try:
            return OrderedDict.__getitem__(self, key)
        except KeyError:
            return self.__missing__(key)

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = value = self.default_factory()
        return value

    def __reduce__(self):
        if self.default_factory is None:
            args = tuple()
        else:
            args = self.default_factory,
        return type(self), args, None, None, self.items()

    def copy(self):
        return self.__copy__()

    def __copy__(self):
        return type(self)(self.default_factory, self)

    def __deepcopy__(self, memo):
        import copy
        return type(self)(self.default_factory,
                          copy.deepcopy(self.items()))

    def __repr__(self):
        return 'OrderedDefaultDict(%s, %s)' % (self.default_factory,
                                               OrderedDict.__repr__(self))


if __name__ == '__main__':
    print(synonymous('exploit'))