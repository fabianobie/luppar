import numpy as np
import nltk
import time
import re
#from textblob import TextBlob
from gensim.models.keyedvectors import KeyedVectors
from gensim.models.word2vec import Word2Vec

from engine.core import Engine
from engine.datasource.medline import Medline
from engine.datasource.npl import NPL
from engine.query import Query, QueryProcessor
from engine.search import VectorSearch, BM25Search
from engine.source import ListSource


def search_basic(source, text, engine=None,total_result=100):
    if not engine:
        preprocess = source.preprocessor
        index = preprocess.get_representation_docs()

        query_processor = QueryProcessor(preprocessor=preprocess)

        search_model = VectorSearch()
        search_model.set_index(index)

        engine = Engine(source, query_processor, search_model, free_search=True)

    query_result = engine.search(text)
    docs_list_retrieval = [source.read_doc(engine.index.get_doc_item(d).id) for d in query_result.docs_retrieval[:total_result]]
    return docs_list_retrieval


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


class AnalysisContextLocal(QueryProcessor):
    '''
        Algorithm of Analysis Context Local
    '''

    def __init__(self, top_docs=None, window_size=300,n_top_ranked = 10, n_passages=20, m_concept=5, factor=0.1,language='en',preprocessor=None):
        self.top_docs = top_docs
        self.window_size = window_size
        self.n_passages = n_passages
        self.m_concept = m_concept
        self.n_top_ranked = n_top_ranked
        self.factor = factor
        self.engine = None
        self.language = language
        self.model = None
        self.passages = []
        super(AnalysisContextLocal, self).__init__(expanded=True, reduce=True, top_docs=top_docs, limit=m_concept,preprocessor = preprocessor)

    @property
    def info(self):
        return 'acl-exp'

    def find_passage(self, window_size, document):
        if self.window_size:
            list_passages = [' '.join(ck) for ck in chunks(document.text.split(), window_size)]
        else:
            list_passages = re.split(r"[.!?;]",' '.join([ck for ck in document.text.split()]))
        return list_passages

    def make_concepts(self,text):
        assert isinstance(text, str)
        is_noun = lambda pos: pos[:2] == 'NN'
        self.engine.preprocessor.pos_tag=True
        return [word for (word, pos) in self.engine.preprocessor.tokenize(text) if is_noun(pos)]

    def find_sort_concepts(self, passages, query):
        millis = int(round(time.time() * 1000))
        source = ListSource(list_docs=passages, list_query=[], language=self.language,info=millis)
        source.preprocessor.use_stop_words = True
        source.preprocessor.save = False
        index = source.preprocessor.get_representation_docs(force=True)
        query_processor = QueryProcessor(expanded=False, reduce=False,preprocessor=source.preprocessor)
        search_model = VectorSearch()
        search_model.set_index(index)
        self.engine = Engine(source, query_processor, search_model, free_search=True)
        query_result = self.engine.search(query)
        docs_list_retrieval = [source.read_doc(self.engine.index.get_doc_item(d).id) for d in
                               query_result.docs_retrieval[:self.n_passages]]
        concepts = []
        for d in docs_list_retrieval:
            concepts.append(self.make_concepts(d.text))

        return concepts

    def func_correlation(self, concept, ki):
        v = self.model[self.engine.index.get_feature_id(concept),self.engine.index.get_feature_id(ki)]
        return v

    def IDF(self,term, N):
        n = len(self.engine.index.index[term])
        return max(1, np.log10(N /n) / 5)

    def exist_vocab(self,k):
        return k in self.engine.index.index.keys()

    def similarity(self, query, concept,i):
        simqc = 0.0
        assert isinstance(query,Query)

        N = len(self.engine.index.documents)
        simqc = []
        for ki in query.query_vector:
            if self.exist_vocab(concept) and self.exist_vocab(ki):
                tmp = (((self.factor + np.log(self.func_correlation(concept, ki))) * self.IDF(concept,N)) / np.log(i+2)) ** self.IDF(ki,N)
                if not np.isinf(tmp) and not np.isnan(tmp):
                    simqc.append(tmp)
        #print(simqc)
        return np.prod(simqc)

    def representation(self):
        self.engine.preprocessor.representation = None
        self.engine.preprocessor.pos_tag = False
        self.engine.index = self.engine.preprocessor.get_representation_docs(do_idf=False, force=True, norm=None,type_tf=3)
        self.model = self.engine.index.comatrix

    def expand_query(self, query):
        if isinstance(query, Query) and len(query.query_vector)>0:
            # Search top documents
            #if not self.top_docs:
            self.top_docs = search_basic(self.preprocessor.source,query.text,total_result=self.n_top_ranked)
            documents = self.top_docs

            # Find passages
            self.passages = []
            if documents:
                for doc in documents:
                    self.passages.extend(self.find_passage(self.window_size, doc))


            # Find concepts
            top_concepts = self.find_sort_concepts(self.passages, query.text)

            self.representation()

            #Sort top concepts
            m_scores = {}
            for i, cpts in enumerate(top_concepts):
                for cpt in cpts:
                    m_scores[cpt] = self.similarity(query,cpt,i)

            #print(m_scores)
            for w in query.query_vector:
                if w in m_scores.keys():
                    del m_scores[w]

            best_m = sorted(m_scores, key=m_scores.get,reverse=True)[:self.m_concept]
            query.query_score = [2.0 for w in query.query_vector]

            print(query.query_vector)
            for i, c in enumerate(best_m):
                query.query_vector.append(c)
                query.query_score.append(1 - (0.9*i/self.m_concept))

            print(query.query_vector)
            return query
        else:
            raise Exception('query is not instance of Query')


class AnalysisContextLocalDSM(AnalysisContextLocal):

    def __init__(self, preprocessor=None):
        super(AnalysisContextLocalDSM, self).__init__(self, window_size=None, preprocessor=preprocessor)

    @property
    def info(self):
        return 'acl-dsm-exp'

    def exist_vocab(self,k):
        return k in self.engine.index.index.keys() and k in self.model.wv.vocab.keys()

    def representation(self):
        if not self.model:
            print("LOAD MODEL...")
            self.model = KeyedVectors.load_word2vec_format(self.preprocessor.source.path + self.preprocessor.source.info+'.model.bin', binary=True)
        pass

    def similarity(self, query, concept,i):
        simqc = 0.0
        assert isinstance(query,Query)

        N = len(self.engine.index.documents)
        simqc = []
        for ki in query.query_vector:
            if self.exist_vocab(concept) and self.exist_vocab(ki):
                tmp = (((self.factor + self.func_correlation(concept, ki)) * self.IDF(concept, N)) / np.log(i + 2)) ** self.IDF(ki, N)
                #tmp = (self.factor+self.func_correlation(concept, ki))
                if not np.isinf(tmp) and not np.isnan(tmp):
                    simqc.append(tmp)

        #print(simqc)
        return np.prod(simqc)


    def func_correlation(self, concept, ki):
        r = self.model.similarity(concept, ki)
        return r


class AnalysisContextLocalDSMGlobal(AnalysisContextLocalDSM):
    @property
    def info(self):
        return 'acl-dsm-exp-l'

    def representation(self):
        self.engine.preprocessor.pos_tag = False
        sentences = [[w for w in self.engine.preprocessor.tokenize(d)] for d in self.passages]
        self.model = Word2Vec(sentences, window=5 ,min_count=1, workers=4)




#
# if __name__ == '__main__':
#     print("Ler source")
#     source = NPL(path='/Users/fabiano/Dropbox/Mestrado/UECE/DISSERTACAO/SISTEMA/luppar/data/npl/')
#     text = 'infantile autism'
#     query = Query(text=text)
#     top_docs = search_basic(source,'infantile autism',total_result=10)
#
#     print("Expansao de consulta")
#     acl = AnalysisContextLocalDSM(m_concept=10, preprocessor=source.preprocessor)
#
#     acl.execute(query)
#
#     print(query.query_vector)
#     print(query.query_score)

