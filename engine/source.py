import abc

from engine.preprocessor import PortuguesePreprocessor, EnglishPreprocessor
from engine.document import Document
from engine.query import Query


class Source(object):
    __metaclass__ = abc.ABCMeta
    __prepro_list = {'pt': PortuguesePreprocessor, 'en': EnglishPreprocessor}

    def __init__(self,local_file_doc,local_file_q,language="en",info=None,preprocessor=None):
        super(Source, self).__init__()
        self.info = info if info else type(self).__name__
        self.local_file_doc = local_file_doc
        self.local_file_q = local_file_q
        self.language = language
        self.preprocessor = preprocessor if preprocessor else self.__prepro_list[self.language](self)

    def get_preprocessor(self):
        return self.preprocessor

    @abc.abstractmethod
    def read_querys(self):
        raise NotImplementedError

    @abc.abstractmethod
    def read_doc(self,id):
        raise NotImplementedError

    @abc.abstractmethod
    def read_docs(self):
        raise NotImplementedError

    @abc.abstractmethod
    def total_querys(self):
        raise NotImplementedError

    @abc.abstractmethod
    def total_docs(self):
        raise NotImplementedError

    @abc.abstractmethod
    def lookup_querys(self, text):
        raise NotImplementedError

    @abc.abstractmethod
    def read_query(self, id):
        raise NotImplementedError

    def print_documents(self):
        for d in self.read_docs():
            print(d)

    def print_querys(self):
        for q in self.read_querys():
            print(q)

    def __str__(self):
        return self.info


class ListSource(Source):

    def __init__(self,list_docs,list_query,language="en",info="ListSource"):
        super(ListSource, self).__init__(local_file_doc=list_docs,local_file_q=list_query,language=language ,info=info)

    def read_querys(self):
        return [Query(id=i,text=q,docs_relevant=docs) for (i,(q, docs)) in enumerate(self.local_file_q)]

    def read_doc(self, id):
        return Document(id=id,text=self.local_file_doc[id])

    def read_docs(self):
        return [Document(id=i,text=v) for i, v in enumerate(self.local_file_doc)]

    def total_querys(self):
        return len(self.local_file_q)

    def total_docs(self):
        return len(self.local_file_doc)

    def lookup_querys(self,text):
        return [Query(id=i,text=q,docs_relevant=docs) for (i,(q, docs)) in enumerate(self.local_file_q) if text in q]

    def read_query(self, id):
        (q, docs) = self.local_file_q[int(id)]
        return Query(id=id, text=q, docs_relevant=docs)


class SampleSource(ListSource):
    def __init__(self,path='', language="en", info="SAMPLE"):
        docs = ['To do is to be. to be is to do',
                'to be or not to be i am what i am',
                'i think therefore i am do be do be do',
                'Do do do da da da let it be let it be']
        qs = [('to do', [0, 1, 2]),
              ('am be', [1, 2])]

        super(SampleSource, self).__init__(list_docs=docs, list_query=qs, language=language, info=info)
