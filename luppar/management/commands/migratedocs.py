import os

from django.core.management.base import BaseCommand

from search_engine.models import SourceType, DocumentData, QueryData
from luppar.settings import BASE_DIR
from engine.util import get_class


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.stdout.write('Init migrate database\n')

        for s in SourceType.objects.filter(slug='artigos', enable=True):
            source = get_class(s.instance)(path=os.path.join(BASE_DIR, s.path))

            for d in source.read_docs():
                if(not DocumentData.objects.filter(idd=d.id,source=s).first()):
                    dd = DocumentData()
                else:
                    dd = DocumentData.objects.filter(idd=d.id,source=s).first()
                dd.idd = d.id
                dd.name = d.name if d.name else 'DOC %s %s' % (s.name,d.id)
                dd.text = d.text.strip()
                if d.name:
                    dd.path = s.path+'/pdf/'+d.name+'.pdf'
                dd.source = s
                dd.prev_text = dd.text[:100]
                dd.save()
                print("Save doc %s %s"%(s.name,d.id))

            for q in source.read_querys():
                if(not QueryData.objects.filter(idq=q.id,source=s)):
                    qd = QueryData()
                else:
                    qd = QueryData.objects.filter(idq=q.id,source=s).first()
                qd.idq = q.id
                qd.text = q.text.strip()
                qd.source = s
                qd.prev_text = qd.text[:100]
                qd.save()
                qd.relevant_docs = [DocumentData.objects.filter(idd=idd, source=s).first() for idd in q.docs_relevant]
                print("Save qry %s %s"%(s.name,q.id))

        self.stdout.write('Save in database all docs files\n')
