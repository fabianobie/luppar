import numpy as np
import time
import re
import os

from gensim.corpora.dictionary import Dictionary
from gensim.models.keyedvectors import KeyedVectors
from gensim.models.lsimodel import LsiModel
from gensim.models.word2vec import Word2Vec

from engine.core import Engine
from engine.query import Query, QueryProcessor
from engine.search import VectorSearch, BM25Search
from engine.source import ListSource
from engine.util import wordsim


def search_basic(source, text, engine=None,total_result=100):
    if not engine:
        preprocess = source.preprocessor
        preprocess.expand_terms=True
        index = preprocess.get_representation_docs()

        query_processor = QueryProcessor(preprocessor=preprocess)

        search_model = BM25Search()
        search_model.set_index(index)

        engine = Engine(source, query_processor, search_model, free_search=True)

    query_result = engine.search(text)
    preprocess.expand_terms = False
    docs_list_retrieval = [source.read_doc(engine.index.get_doc_item(d).id) for d in query_result.docs_retrieval[:total_result]]
    return docs_list_retrieval


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


class AnalysisContextLocal(QueryProcessor):
    '''
        Algorithm of Analysis Context Local
    '''

    def __init__(self, top_docs=None, window_size=300,  n_top_ranked=10, n_passages=50, m_concept=5, factor=0.0001, preprocessor=None):
        self.top_docs = top_docs
        self.window_size = window_size
        self.n_passages = n_passages
        self.m_concept = m_concept
        self.n_top_ranked = n_top_ranked
        self.factor = factor
        self.engine = None
        self.language = preprocessor.lang
        self.model = None
        self.passages = []
        super(AnalysisContextLocal, self).__init__(expanded=True, reduce=True, top_docs=top_docs, limit=m_concept, preprocessor=preprocessor)

    @property
    def info(self):
        return 'acl-exp'

    def find_passage(self, window_size, document):
        list_passages = []
        if window_size:
            list_passages = [' '.join(ck) for ck in chunks(document.text.split(), window_size)]
        else:
            list_passages_tmp = [p for p in re.split(r"[.!?;]\s", ' '.join(document.text.splitlines())) if len(p) > 10]
            i = 0
            r = ''
            list_passages = []
            for p in list_passages_tmp:
                if i > 5:
                    i = 0
                    list_passages.append(r)
                    r = ''
                else:
                    r += ' ' + p
                    i += 1
            if i<=5 and i>0:
                list_passages.append(r)
        return list_passages

    def make_concepts(self,text):
        assert isinstance(text, str)
        is_noun = lambda pos: pos[:2] == 'NN'
        self.engine.preprocessor.pos_tag=True

        return [word for (word, pos) in self.engine.preprocessor.tokenize(text) if is_noun(pos) and len(word)>2]

    def find_sort_concepts(self, passages, query):
        millis = int(round(time.time() * 1000))
        source = ListSource(list_docs=passages, list_query=[], language=self.language,info=millis)
        source.preprocessor.use_stop_words = True
        source.preprocessor.save = False
        source.preprocessor.reduce = True
        source.preprocessor.pos_tag = False
        source.preprocessor.expand_terms = True
        index = source.preprocessor.get_representation_docs(force=True,do_idf=False,type_tf=3,norm=None)
        query_processor = QueryProcessor(expanded=False, reduce=True, preprocessor=source.preprocessor)
        search_model = VectorSearch()
        search_model.set_index(index)
        self.engine = Engine(source, query_processor, search_model, free_search=True)
        query_result = self.engine.search(query)
        docs_list_retrieval = [source.read_doc(d) for d in query_result.docs_retrieval[:self.n_passages]]
        concepts = []
        for d in docs_list_retrieval:
            concepts.extend(self.make_concepts(d.text))

        return list(set(c for c in concepts))

    def func_correlation(self, concept, ki):
        try:
            r = self.model[self.engine.index.get_feature_id(concept),self.engine.index.get_feature_id(ki)]
            #print(r)
            if r < 0:
                #print("Erro palavra negativo")
                return 0.0
            else:
                return r
        except:
            #print("Erro palavra nao index correlacao")
            return 0


    def IDF(self,term, N, Nc):
        return min(1, np.log10(N / Nc) / 5)

    def exist_vocab(self,k):
        return k in self.engine.index.index.keys()

    def co_degree(self,c,ki,N,Nc):
        return np.log10(self.func_correlation(c, ki)+1) * self.IDF(c,N,Nc) / np.log10(self.n_top_ranked)

    def similarity(self, query, concept):
        assert isinstance(query,Query)

        N = len(self.preprocessor.representation.documents)
        try:
            Nc = len(self.preprocessor.representation.index[concept])
        except:
            #print("Erro palavra nao index")
            return 0.0

        simqc = []
        for ki in query.query_vector:
            try:
                Nk = len(self.preprocessor.representation.index[ki])
            except:
                #print("Erro palavra nao index local")
                continue
            tmp = (self.factor + self.co_degree(concept, ki, N, Nc)) ** self.IDF(ki, N, Nk)
            simqc.append(tmp)
        #print('%s: %s' % (concept,simqc))
        return np.prod(simqc)

    def representation(self):
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
            for i, cpt in enumerate(top_concepts):
                    m_scores[cpt] = self.similarity(query,cpt)

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

    def __init__(self, preprocessor=None,w=5,s=100):
        self.w=w
        self.s=s
        super(AnalysisContextLocalDSM, self).__init__(self,  window_size=None, n_top_ranked=10, n_passages=50, m_concept=5, factor=0.0001, preprocessor=preprocessor)

    @property
    def info(self):
        return 'acl-dsm-exp'

    def exist_vocab(self,k):
        return k in self.engine.index.index.keys() and k in self.model.wv.vocab.keys()


    def representation(self):
        if not self.model:
            print("LOAD MODEL... %s x %s"%(self.w,self.s))
            try:
                self.model = KeyedVectors.load_word2vec_format(
                    os.path.join(self.preprocessor.source.path, self.preprocessor.source.info + '.model.bin'),
                    binary=True)
            except:
                self.model = KeyedVectors.load_word2vec_format(os.path.join(self.preprocessor.source.path,
                                                                            self.preprocessor.source.info + (
                                                                            '%s_%s.model.bin' % (self.w, self.s))),
                                                               binary=True)

        pass

    def vector_sim(self, wdoc, wquery):
        return np.dot(wdoc,wquery)/(np.linalg.norm(wdoc)*np.linalg.norm(wquery))

    def co_degree(self,c,ki,N,Nc):
        return np.log10(self.func_correlation(c, ki) + 1) * self.IDF(c,N,Nc) / np.log10(self.n_top_ranked)
        #return (self.func_correlation(c, ki)+1)

    def func_correlation(self, concept, ki):
        try:
            r = self.model.wv.similarity(concept, ki)
            if r < 0:
                return r
            else:
                return r
        except:
            return -1

    def similarity(self, query, concept):
        assert isinstance(query,Query)

        N = len(self.preprocessor.representation.documents)
        try:
            Nc = len(self.preprocessor.representation.index[concept])
        except:
            return -1.0

        simqc = []
        for ki in query.query_vector:
            try:
                Nk = len(self.preprocessor.representation.index[ki])
            except:
                continue
            tmp = (self.factor + self.co_degree(concept, ki, N, Nc)) # ** self.IDF(ki, N, Nk)
            simqc.append(tmp)
        #print('%s: %s' % (concept,simqc))
        #print('%s: %s' % (concept, np.prod(simqc)))

        #self.preprocessor.expand_terms = True
        return np.prod(simqc)


class AnalysisContextLocalDSMLocal(AnalysisContextLocalDSM):
    @property
    def info(self):
        return 'acl-dsm-exp'

    def representation(self):
        self.engine.preprocessor.pos_tag = False
        sentences = [[w for w in self.engine.preprocessor.tokenize(d)] for d in self.passages]
        self.model = Word2Vec(sentences, window=3, min_count=1, workers=4)

class AnalysisContextLocalDSMw2v(AnalysisContextLocalDSM):
    @property
    def info(self):
        return 'acl-dsm-exp-w2v'

    def expand_query(self, query):
        if isinstance(query, Query) and len(query.query_vector)>0:

            self.representation()

            res = self.model.most_similar(positive=[k for k in query.query_vector if k in self.model.wv.vocab.keys()],topn=self.m_concept)

            best_m = [r for r,i in res]
            query.query_score = [2.0 for w in query.query_vector]

            print(query.query_vector)
            for i, c in enumerate(best_m):
                query.query_vector.append(c)
                query.query_score.append(1 - (0.9*i/self.m_concept))

            print(query.query_vector)
            return query
        else:
            raise Exception('query is not instance of Query')


class AnalysisContextLocalDSMGlobal(QueryProcessor):
        @property
        def info(self):
            return 'acl-dsm-exp-co'

        def exist_vocab(self, k):
            return k in self.engine.index.index.keys() and k in self.preprocessor.representation.index.keys()

        def representation(self):
            self.model = self.preprocessor.representation.comatrix


class AnalysisContextLocalLsa(QueryProcessor):
            @property
            def info(self):
                return 'acl-lsa-exp'

            def representation(self):
                if not self.model:
                    print("LOAD MODEL...")
                    self.model = LsiModel.load(os.path.join(self.preprocessor.source.path, self.preprocessor.source.info + '.model'))
                    self.dictionary = Dictionary.load(os.path.join(self.preprocessor.source.path, self.preprocessor.source.info + '.dic'))
                pass

            def exist_vocab(self, k):
                return k in self.engine.index.index.keys() and k in self.preprocessor.representation.index.keys()

            def func_correlation(self, concept, ki):
                try:
                    return wordsim(ki,concept,self.dictionary,self.model)
                except:
                    print('Erro')
                    return 0



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
