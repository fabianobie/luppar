# -*- coding: utf-8 -*-
from os import popen

from engine.datasource.medline import Medline
from engine.eval.eval_results import EvaluationResult
from engine.preprocessor import PortuguesePreprocessor
from engine.query import Query



TREC_EVAL_COMMAND = "/usr/local/bin/trec_eval -q -c %s %s"


class Engine(object):

    def __init__(self,source,query_processor,search_model,context=None,force=False,expanded=False,free_search=True):
        self.source = source
        self.language = source.language
        self.search_model = search_model
        self.context = context

        self.preprocessor = self.source.preprocessor
        self.query_processor = query_processor
        self.index = self.preprocessor.get_representation_docs()
        self.search_model.set_index(self.index)

        self.querys = self.preprocessor.get_representation_query()
        self.free_search = free_search
        self.query = None

    def search(self, text, qid=None, related_docs=None):
        query = Query()
        if(not self.free_search):
            if qid==None:
                for q in self.preprocessor.get_representation_query():
                    if(q.text==text):
                        query = q
                        break
            else:
                qtmp = self.source.read_query(qid)
                query.text = qtmp.text
                query.docs_relevant = qtmp.docs_relevant
                query.docs_retrieval = []


        if self.free_search or query.text=='':
            query.text = text

        self.query_processor.execute(query)
        documents = self.search_model.retrieval(query, related_docs)
        if len(documents)==2:
            query.docs_retrieval = documents[0]
            query.docs_scores = documents[1]
        else:
            query.docs_retrieval = documents
            query.docs_scores = []
        self.query = query
        return query

    def slug(self):
        return str("%s_%s_%s_%s_%s"%(self.source,self.search_model.info,self.search_model.params['mode'],self.query_processor.info,self.query_processor.reduce)).lower()

    def __str__(self):
        return "Source: %s \n Query: %s \n Model: %s \n Expansion: %s \n Context: %s" \
               % (self.source,self.query.query_vector,self.search_model, self.query_processor,self.context)

    def calculate_metrics(self, query_result, id = ''):
        name = '%s_%s'%(self.slug(),id)
        path_retrieval_file = '/tmp/%s.RET' % name
        path_relevant_file = '/tmp/%s.REL' % name
        path_result_file = '/tmp/%s.RES' % name

        fo_rel = open(path_relevant_file, 'w')
        fo_ret = open(path_retrieval_file, 'w')

        docs_list_retrieval = [self.index.get_doc_item(d).id for d in query_result.docs_retrieval]
        docs_list_relevant = [d for d in query_result.docs_relevant]
        docs_score_relevant = [v for v in query_result.docs_scores]

        for i, d in enumerate(docs_list_relevant):
            fo_rel.write('%d 0 %s %d\n' % (1, d, 1)) #query_result.id

        for i, (d, s) in enumerate(zip(docs_list_retrieval, docs_score_relevant)):
            fo_ret.write('%d Q0 %s %d %f %s\n' % (1, d, i, s, self.source.info)) #query_result.id

        fo_rel.close()
        fo_ret.close()

        output = popen(TREC_EVAL_COMMAND % (path_relevant_file, path_retrieval_file))
        fo = open(path_result_file, 'wt')

        for linha in output:
            fo.write(linha)
        fo.close()

        ev = EvaluationResult(path_result_file)

        return ev.results

