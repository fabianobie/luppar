from engine import Source
import re

from engine.document import Document
from engine.preprocessor import EnglishPreprocessor
from engine.query import Query

class Lisa(Source):
    _pattern = r'\n?Document(\s*)(?P<id>\d*)\n(?P<text>.*)'
    _pattern_qry = r'^\n?(?P<id>\d*)(?P<text>.*)'
    _pattern_rel = r'^(\n*?)Query (?P<id>\d.*)\n(\d.*)Relevant Refs:(?P<text>.*)'
    _id_files = [1, 501, 1001, 1501, 2001, 2501, 3001, 3501, 4001, 4501, 5001, 5501, 5627, 5850]

    def __init__(self,path):
        self.path = path
        self.__querys = None
        self.__docs = None
        self.preprocessor = EnglishPreprocessor(self, use_stop_words=True)
        super(Lisa, self).__init__(local_file_doc=path + '/LISA%s', local_file_q=path + '/LISA.QUE', language="en",info="LISA", preprocessor=self.preprocessor)

    def read_querys(self):
        if(not self.__querys):
            files = open(self.local_file_q, 'r').read().split('#')
            self.__querys = dict()
            for line in files:
                match = re.match(self._pattern_qry, line, re.DOTALL)
                if match:
                    new_line = match.groupdict()
                    if(new_line['id']):
                        self.__querys[int(new_line['id'])] = Query(id=int(new_line['id']),text=str(new_line['text'].strip()))

            relevants = open(self.path+'/LISA.REL', 'r').read().split('-1')
            for line in relevants:
                match = re.match(self._pattern_rel, line, re.DOTALL)
                if match:
                    new_line = match.groupdict()
                    if (new_line['id']):
                        key = int(new_line['id'])
                        self.__querys[int(key)].docs_relevant = list(map(int,new_line['text'].split()))

        return self.__querys.values()


    def read_doc(self, id):
        if (not self.__docs):
            for d in self.read_docs(idref=id):
                if(d.id==id):
                    return d
        else:
            return self.__docs[int(id)]


    def read_docs(self,idref=None):
        if (not self.__docs):
            self.__docs = dict()
            ids_doc = []
            if idref:
                ids_doc.append(['%04.3f'%(id/1000) for id in self._id_files if idref >= id][-1])
            else:
                ids_doc = ['%04.3f'%(id/1000) for id in self._id_files]
            for id in ids_doc:
                files = open(self.local_file_doc % id, 'r').read().split('********************************************')
                for line in files:
                    match = re.match(self._pattern, line, re.DOTALL)
                    if match:
                        new_line = match.groupdict()
                        if (new_line['id']):
                            d = Document(id=int(new_line['id']),text=new_line['text'])
                            #self.__docs[d.id] = d
                            yield d

        #return self.__docs.values()
        else:
            for d in self.__docs.values():
                yield d



    def total_querys(self):
        return len(self.read_querys())

    def total_docs(self):
        return  len([d for d in self.read_docs()])

    def lookup_querys(self,text):
        return [q for q in self.read_querys() if text.lower() in q.text.lower()]

    def read_query(self, id):
        for q in self.read_querys():
            if q.id == id:
                return q
        return None




