from engine import Source
import re
import numpy as np

from engine.document import Document
from engine.preprocessor import EnglishPreprocessor
from engine.query import Query


class Cisi(Source):
    _pattern = r'^(\.I)?\s(?P<id>\d*)(.*?)\.T(?P<title>.*)(.*?)\.A(.*?)\.W(?P<text>.*)\.X'

    _pattern_qry = r'^\s(?P<id>\d*)(.*?)\.W(?P<text>.*)'
    _pattern_qry2 = r'^\s(?P<id>\d*)(.*?)\.W(?P<text>.*)\.B'

    def __init__(self,path):
        self.path = path
        self.__querys = None
        self.__docs = None
        self.preprocessor = EnglishPreprocessor(self, use_stop_words=True)
        super(Cisi, self).__init__(local_file_doc=path + '/CISI.ALL', local_file_q=path + '/CISI.QRY', language="en",info="CISI", preprocessor=self.preprocessor)


    def read_querys(self):
        if(not self.__querys):
            files = open(self.local_file_q, 'r').read().split('.I')
            self.__querys = dict()
            for line in files:
                if line:
                    pttq = self._pattern_qry2 if '.B' in line else self._pattern_qry
                    match = re.match(pttq, line, re.DOTALL)
                    if match:
                        new_line = match.groupdict()
                        self.__querys[int(new_line['id'])] = Query(id=int(new_line['id']),text=str(new_line['text'].strip()))
                    else:
                        print("Not match qry"+line)

            relevants = open(self.path+'/CISI.REL', 'r').readlines()
            for i in relevants:
                line = np.array(i.split()).tolist()
                key = int(line[0])
                if key in self.__querys:
                    self.__querys[int(key)].docs_relevant.append(int(line[1]))

            for k in list(self.__querys.keys()):
                if not self.__querys[k].docs_relevant:
                    del self.__querys[k]

        return self.__querys.values()


    def read_doc(self, id):
        if (not self.__docs):
            for d in self.read_docs():
                if(d.id==id):
                    return d
        else:
            return self.__docs[int(id)]

    def read_docs(self):
        if (not self.__docs):
            self.__docs = dict()
            files = re.compile('\n\.I').split(open(self.local_file_doc, 'r').read())
            for line in files:
                match = re.match(self._pattern, line, re.DOTALL)
                if match:
                    new_line = match.groupdict()
                    d = Document(id=new_line['id'],text=new_line['title']+new_line['text'])
                    self.__docs[d.id] = d
                    yield d
                else:
                    if line.strip(): print("Not match " + line)
        else:
            for d in self.__docs.values():
                yield d

    def total_querys(self):
        return len(self.read_querys())

    def total_docs(self):
        return len([d for d in self.read_docs()])

    def lookup_querys(self,text):
        return [q for q in self.read_querys() if text in q.text]

    def read_query(self, id):
        for q in self.read_querys():
            if q.id == id:
                return q
        return None




