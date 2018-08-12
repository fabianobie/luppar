import json
import operator

import nltk

from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords

from engine.preprocessor import EnglishPreprocessor, PortuguesePreprocessor


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

    def dic_vector(self):
        if self.query_score:
            return {w: float(format(s, '.2f')) for w,s in zip(self.query_vector,self.query_score)}
        return {w: 1.0 for w in self.query_vector}



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
            # if self.expanded:
            #     self.preprocessor.expand_terms = True

            tokens = self.preprocessor.tokenize(query.text)
            if self.reduce:
                tokens = [tr for tr, tg in tokens if 'NN' in tg or 'JJ' in tg or 'VB' in tg or 'RB' in tg]
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

    @property
    def lang(self):
        if self.preprocessor:
            if self.preprocessor.lang=='pt-br':
                return 'por'
            elif self.preprocessor.lang=='es':
                return 'spa'
            else:
                return 'eng'
        else:
            return 'eng'

    def preExpand(self, word):
        self.preprocessor.pos_tag = True
        word = self.preprocessor.tokenize(word)
        if word:
            tagged = word[0][1]
            if tagged == "VB":
                result = wn.VERB
            elif tagged == "RB":
                result = wn.ADJ
            elif tagged == "JJ":
                result = wn.ADV
            else:
                result = wn.NOUN
            self.preprocessor.pos_tag = False
            return result
        else:
            return None

    def expand_query(self, query):
        result = ""
        assert isinstance(query,Query)

        for word in nltk.tokenize.word_tokenize(query.text):
            if len(word) > 2:
                result = result + word + " "
                for w in word.split('_'):
                    if len(word) > 2:
                        key = self.preExpand(w)
                        if key:
                            syncs = wn.synsets(w, pos=key, lang=self.lang)
                            if len(syncs)>0 :
                                datas = syncs[0].lemma_names(self.lang)
                                for data in datas:
                                    if data.lower() == word.lower():
                                        continue
                                    result = result + data + " "

        self.preprocessor.pos_tag=False
        query.query_vector = list(set(self.preprocessor.tokenize(result)))
        print(query.query_vector)
        return query

if __name__ == '__main__':
    # print("Teste")
    # query_result={1:0.1,3:0.6,2:0.3,4:0.9,5:0.2}
    # query_result_sorted = sorted(query_result.items(), key=operator.itemgetter(1), reverse=True)
    palavra = "infantile"

    preprocessor = EnglishPreprocessor(source=None)
    word = preprocessor.tokenize(palavra)
    tagged = nltk.pos_tag(word)[0][1]

    syns = wn.synsets(palavra,lang='eng',pos=wn.NOUN)

    for w in syns:
        # An example of a synset:
        print(w.name())

        # Just the word:
        print(w.lemmas()[0].name())

        # Definition of that first synset:
        print(w.definition())

        # Examples of the word in use in sentences:
        print(w.examples())

        print(w.lemma_names('eng'))

