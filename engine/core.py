# -*- coding: utf-8 -*-

from engine.query import Query


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


    def search(self, text,qid=None):
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
        documents = self.search_model.retrieval(query)
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