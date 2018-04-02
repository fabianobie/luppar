import json
import operator

import nltk

from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords

from engine.preprocessor import EnglishPreprocessor


class Query(object):

    def __init__(self, id=None,text='', pos_tag=False,query_vector=None,docs_relevant=None,docs_retrieval=None):
        super(Query,self).__init__()
        self.id = id
        self.text = text
        self.query_vector = query_vector if query_vector else []
        self.docs_relevant = docs_relevant if docs_relevant else []
        self.docs_retrieval = docs_retrieval if docs_retrieval else []
        self.docs_scores = []
        self.query_score = []
        self.pos_tag = pos_tag

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

    def __str__(self):
        return self.text+" "+str(self.docs_relevant)


class QueryProcessor(object):

    def __init__(self,expanded=False,limit=10,reduce=True,top_docs=None,preprocessor=None):
        self.expanded = expanded
        self.limit = limit
        self.reduce = reduce
        self.top_docs = top_docs
        self.preprocessor = preprocessor

    @property
    def info(self):
        return 'no-exp'

    def expand_query(self,text):
        raise NotImplementedError

    def execute(self, query):
        if(isinstance(query,Query) and self.preprocessor):
            self.preprocessor.pos_tag = self.reduce

            tokens = self.preprocessor.tokenize(query.text)
            if self.reduce:
                tokens = [tr for tr, tg in tokens if 'NN' in tg or 'JJ' in tg or 'VB' in tg]
            query.query_vector = tokens

            if self.expanded:
                query = self.expand_query(query)
        else:
            raise Exception('Not a Query object or havent Preprocessor')

    def __str__(self):
        return type(self).__name__

class WordnetQueryProcess(QueryProcessor):
    def __init__(self, language="en",preprocessor=None,limit=2):
        super(WordnetQueryProcess, self).__init__(expanded=True,reduce=True,top_docs=None,limit=limit,preprocessor=preprocessor)

    @property
    def info(self):
        return 'wn-exp'

    def preExpand(self, word):
        word = nltk.word_tokenize(word)
        tagged = nltk.pos_tag(word)[0][1]
        if tagged == "VB":
            result = wn.VERB
        elif tagged == "RB":
            result = wn.ADJ
        elif tagged == "JJ":
            result = wn.ADV
        else:
            result = wn.NOUN
        return result

    def expand_query(self, query):
        result = ""
        assert isinstance(query,Query)

        for word in query.text.split():
            result = result + word + " "
            key = self.preExpand(word)
            if word.lower() not in stopwords.words():
                datas = wn.synsets(word, pos=key)
                for data in datas:
                    stripedWord = str(data).split('.')[0].split("'")[1]
                    if stripedWord == word:
                        continue
                    result = result + stripedWord + " "

        self.preprocessor.pos_tag=False
        query.query_vector = list(set(self.preprocessor.tokenize(result)))
        return query

if __name__ == '__main__':
    print("Teste")
    query_result={1:0.1,3:0.6,2:0.3,4:0.9,5:0.2}
    query_result_sorted = sorted(query_result.items(), key=operator.itemgetter(1), reverse=True)