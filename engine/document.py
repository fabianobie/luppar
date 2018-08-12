

class Document(object):
    def __init__(self, id,text='',text_vector=None,name=None):
        super(Document,self).__init__()
        self.id = int(id)
        self.name = name
        self.text = text
        self.text_vector = text_vector if text_vector else []
        self.text_prev = text[:60]

    @property
    def size(self):
        return len(self.text)

    def __str__(self):
        return str(self.id)+" - "+ self.text