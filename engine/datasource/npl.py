from engine import Source
import re

from engine.document import Document
from engine.preprocessor import EnglishPreprocessor
from engine.query import Query

class NPL(Source):
    _pattern = r'^\n?(?P<id>\d*)(?P<text>.*)'

    def __init__(self,path):
        self.path = path
        self.__querys = None
        self.__docs = None
        self.preprocessor = EnglishPreprocessor(self, use_stop_words=True)
        super(NPL, self).__init__(local_file_doc=path + '/doc-text', local_file_q=path + '/query-text', language="en",info="NPL", preprocessor=self.preprocessor)

    def read_querys(self):
        if(not self.__querys):
            files = open(self.local_file_q, 'r').read().split('/')
            self.__querys = dict()
            for line in files:
                match = re.match(self._pattern, line, re.DOTALL)
                if match:
                    new_line = match.groupdict()
                    if(new_line['id']):
                        self.__querys[int(new_line['id'])] = Query(id=int(new_line['id']),text=str(new_line['text'].strip()))

            relevants = open(self.path+'/rlv-ass', 'r').read().split('/')
            for line in relevants:
                match = re.match(self._pattern, line, re.DOTALL)
                if match:
                    new_line = match.groupdict()
                    if (new_line['id']):
                        key = int(new_line['id'])
                        self.__querys[int(key)].docs_relevant = list(map(int,new_line['text'].split()))

        return self.__querys.values()


    def read_doc(self, id):
        if (not self.__docs):
            files = open(self.local_file_doc, 'r').read().split('/')
            for line in files:
                match = re.match(self._pattern, line, re.DOTALL)
                if match:
                    new_line = match.groupdict()
                    if(int(new_line['id'])==int(id)):
                        return Document(id=new_line['id'],text=new_line['text'])
        else:
            return self.__docs[int(id)]

    def read_docs(self):
        if (not self.__docs):
            self.__docs = dict()
            files = open(self.local_file_doc, 'r').read().split('/')
            for line in files:
                match = re.match(self._pattern, line, re.DOTALL)
                if match:
                    new_line = match.groupdict()
                    if (new_line['id']):
                        d = Document(id=int(new_line['id']),text=new_line['text'])
                        self.__docs[d.id] = d
                        yield d

        #return self.__docs.values()
        else:
            for d in self.__docs.values():
                yield d



    def total_querys(self):
        files = open(self.local_file_q, 'r').read().split('/')
        return len(files)-1

    def total_docs(self):
        files = open(self.local_file_doc, 'r').read().split('/')
        return len(files)-1

    def lookup_querys(self,text):
        return [q for q in self.read_querys() if text.lower() in q.text.lower()]

    def read_query(self, id):
        for q in self.read_querys():
            if q.id == id:
                return q
        return None


# if __name__ == '__main__':
#     _pattern = r'^\n?(?P<id>\d*)(?P<text>.*)'
#     line='''93
# HIGH FREQUENCY OSCILLATORS USING TRANSISTORS THEORETICAL TREATMENT AND PRACTICAL CIRCUIT DETAILS
#     '''
#
#     match = re.match(_pattern, line, re.DOTALL)
#     new_line = match.groupdict()
#     print str(new_line)


