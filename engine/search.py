import numpy as np
import abc
import math
import operator

from gensim.models.keyedvectors import KeyedVectors


class AbstractSearch(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self,params=None,info=None):
        super(AbstractSearch, self).__init__()
        self.params = params if params!=None else dict()
        self.info = info

    def set_index(self,index):
        self.index = index
        if self.index:
            self.matrix = self.index.tf_idf()

    @abc.abstractmethod
    def retrieval(self,query):
        raise NotImplementedError

    def validate(self,query):
        if (not self.index):
            raise Exception('Index not defined')

        if query.query_vector==None:
            raise Exception('Use query processor in query not defined')

    def __str__(self):
        return self.info

    def rocchio_method(self, wq, related_docs):
        alpha = 1
        beta = 2
        Nr = len(related_docs)
        list_docs = np.array([self.matrix[self.index.get_doc_item_by_id(did),:] for did in related_docs][0].toarray())

        qm = alpha * wq + (beta / Nr)*np.sum(list_docs, axis=0)
        return qm



class BooleanSearch(AbstractSearch):

    def __init__(self, index=None, params=None, info='BOOL'):
        super(BooleanSearch, self).__init__(params=params,info=info)
        self.set_index(index)

        if 'mode' not in self.params:
            self.params['mode'] = 'or'


    def retrieval(self, query, related_docs = None):
        self.validate(query)

        mode = self.params['mode']
        result_docs = []
        doc_list = []

        for term in query.query_vector:
            doc_list.append(self.index.lookup(term))

        if (mode == "and"):
            result_docs = set(doc_list[0]).intersection(*doc_list)
        elif (mode == "or"):
            for i in doc_list:
                result_docs += i
        elif (mode == "nor"):
            factor = 0.5
            for term in query.query_vector:
                try:
                    key = self.index.get_feature_id(term)
                    s = [i if i > 0.01 else 0 for i in self.index.matrix[:,key].toarray()]
                    sum_s = sum(s)
                    #TODO verify when everbody is ZERO
                    norm = [float(i) / sum_s if sum_s > 0 else 0.5 for i in s]
                    tmp = 0
                    s_id_sorted = sorted(range(len(norm)), key=lambda k: norm[k], reverse=True)
                    for sid in s_id_sorted:
                        if tmp <= factor:
                            tmp += norm[sid]
                            result_docs.append(sid)
                        else:
                            break
                except:
                    continue

        # print result_docs
        result_docs = list(set(result_docs))
        return (result_docs, [0.0001 for d in result_docs])



class VectorSearch(BooleanSearch):

    def __init__(self, params=None, info='VSM'):
        super(VectorSearch, self).__init__(params=params, info=info)

    def retrieval(self, query, related_docs = None):
        list_doc,x = super(VectorSearch, self).retrieval(query)
        query_result = dict()

        query_result_sorted = []
        if list_doc:
            wquery = self.index.query_tf_idf(query,do_idf=False,type_tf=3,norm=None).toarray()[0]

            if(related_docs):
                wquery = self.rocchio_method(wquery,related_docs)

            for docid in list_doc:
                wdoc = self.matrix[docid,:].toarray()
                score = self.vector_sim(wdoc,wquery)
                query_result[docid] = score

            query_result_sorted = sorted(query_result.items(), key=operator.itemgetter(1), reverse=True)

        return ([d[0] for d in query_result_sorted],[d[1] for d in query_result_sorted])

    def vector_sim(self, wdoc, wquery):
        return np.dot(wdoc,wquery)/(np.linalg.norm(wdoc)*np.linalg.norm(wquery))




class BM25Search(BooleanSearch):

    def __init__(self, params=None, info='BM25'):
        super(BM25Search, self).__init__(params=params, info=info)
        self.query = None
        self.wquery = None

        if 'k1' not in self.params:
            self.params['k1'] = 2.0

        if 'k3' not in self.params:
            self.params['k3'] = 1.0

        if 'b' not in self.params:
            self.params['b'] = 0.75

    def retrieval(self, query, related_docs = None):
        list_doc,x = super(BM25Search, self).retrieval(query)
        self.query = query
        query_result = dict()

        if self.query.query_score:
            self.wquery = self.index.query_tf_idf(query,do_idf=True,type_tf=1,norm=None).toarray()[0]

            if (related_docs):
                self.wquery = self.rocchio_method(self.wquery, related_docs)

        for docid in list_doc:
            for q in query.query_vector:
                if (q in self.index.feature_names.values()):
                    score = self.BM25(docid, self.index.get_feature_id(q))
                    if (not docid in query_result):
                        query_result[docid] = score
                    else:
                        query_result[docid] = query_result[docid] + score

        query_result_sorted = sorted(query_result.items(), key=operator.itemgetter(1), reverse=True)

        return ([d[0] for d in query_result_sorted], [d[1] for d in query_result_sorted])

    def BM25(self, docid, qid):
        df = self.calc_df(qid)
        tf = self.calc_tf(docid, qid)
        dsize = self.index.documents[docid].size
        avg_dsize = self.index.avg_docs()
        N = len(self.index.documents)
        freq_Q = self.calc_qf(qid)

        result = freq_Q * self.idf(N, df) * ((tf * (self.params['k1'] + 1)) / (tf + self.params['k1'] * (1 - self.params['b'] + self.params['b'] * (dsize / avg_dsize))))
        return result

    def idf(self, N, df, base=10):
        return math.log((N - df + 0.5) / (df + 0.5),base)

    def calc_df(self, qid):
        term = self.index.feature_names[qid]
        docs = self.index.index[term]
        return len(docs)

    def calc_tf(self, docid, qid):
        return self.index.term_doc_freq(qid,docid)

    def calc_qf(self,qid):
        if len(self.query.query_score) == 0:
            return 1
        else:
            return ((self.params['k3']+1)*self.wquery[qid])/(self.params['k3']+self.wquery[qid])



def vsm(wdoc, wquery):
    return np.dot(wdoc, wquery) / (np.linalg.norm(wdoc) * np.linalg.norm(wquery))
if __name__ == '__main__':
     v1 = np.array([2,0])
     v2 = np.array([1,2])
     v3 = np.array([1,5])
     print(np.sum([v1,v2,v3], axis=0)/2)
