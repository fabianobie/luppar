# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

import os
import traceback

import sys
from django.contrib import messages
from django.contrib.messages.constants import INFO,SUCCESS,WARNING,ERROR
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core import serializers
from django.http.response import HttpResponse
from django.utils.translation import ugettext as _

from django.views.generic.base import TemplateView

from datetime import datetime

from engine.core import Engine
from engine.util import get_class
from luppar.settings import BASE_DIR
from search_engine.models import SourceType, SearchType, QueryProcessorType, QueryData, DocumentData, QueryRequest


def query_preview(request):
    list_q = []
    if('q' in request.GET.keys() and 's' in request.GET.keys()):
        q = str(request.GET['q'])
        s = str(request.GET['s'])
        src_type = SourceType.objects.filter(slug=s).first()

        if len(q)<3 or src_type.slug == 'test':
            list_q = QueryData.objects.filter(text__contains=q, source=src_type)[:10]
        else:
            list_q = QueryData.objects.filter(text__search=q+'*',source=src_type)[:10]

        data = serializers.serialize('json', list_q)
    return HttpResponse(data, content_type="application/json")


class IndexView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        context['source_list'] = SourceType.objects.filter(enable=True)
        context['query_processor_list'] = QueryProcessorType.objects.filter(enable=True)
        context['search_list'] = SearchType.objects.filter(enable=True)
        context['message_hi'] = _("Welcome to Luppar Search !")

        if not ('source_select' in self.request.session.keys()):
            self.request.session['source_select'] = 'test'
            self.request.session['query_processor_select'] = 'no-expansion'
            self.request.session['search_model_select'] = 'bm25'
            self.request.session['free_search'] = 'off'

        context['result_config'] = ''
        context['query_text'] = ''

        session2context(context,self.request.session)
        return context

class AboutView(TemplateView):
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        context = super(AboutView, self).get_context_data(**kwargs)

        return context

class ResultView(TemplateView):
    template_name = 'result.html'

    def get_context_data(self, **kwargs):
        context = super(ResultView, self).get_context_data(**kwargs)

        return context


class SearchView(IndexView):

    def get_context_data(self, **kwargs):

        context = super(SearchView, self).get_context_data(**kwargs)
        source_select = self.request.GET['source_select'] if 'source_select' in self.request.GET.keys() and self.request.GET['source_select'] else None
        query_processor_select = self.request.GET['query_processor'] if 'query_processor' in self.request.GET.keys() and self.request.GET['query_processor'] else None
        search_model_select = self.request.GET['search_model'] if 'search_model' in self.request.GET.keys() and self.request.GET['search_model'] else None
        query_text = self.request.GET['q'] if 'q' in self.request.GET.keys() and self.request.GET['q'] else None
        qid = int(self.request.GET['qid']) if 'qid' in self.request.GET.keys() and self.request.GET['qid'] else None
        page = int(self.request.GET['page']) if 'page' in self.request.GET.keys() and self.request.GET['page'] else 1
        free_search = True if 'free_search' in self.request.GET.keys() and self.request.GET['free_search']=='on' else False

        try:
            if(source_select and query_processor_select and search_model_select and query_text):
                  source = SOURCES_LIST[source_select]
                  source_type =  SourceType.objects.filter(slug=source_select).first()
                  q_pro_type = QueryProcessorType.objects.filter(slug=query_processor_select).first()
                  query_processor = get_class(q_pro_type.instance)(preprocessor=source.preprocessor)

                  search_type = SearchType.objects.filter(slug=search_model_select).first()
                  search_model = get_class(search_type.instance)()

                  engine = Engine(source,query_processor,search_model,free_search=free_search)

                  now = datetime.now()
                  query_result = engine.search(query_text,qid=qid)
                  later = datetime.now()

                  diff = later - now
                  diff_in_seconds = diff.seconds + diff.microseconds/1E6

                  docs_list = query_result.docs_retrieval
                  docs_list_relevant = query_result.docs_relevant

                  context['total_docs'] = len(docs_list)
                  paginator = Paginator(docs_list, 10)
                  paginator2 = Paginator(docs_list_relevant, 10)

                  try:
                      docs = paginator.page(page)
                  except PageNotAnInteger:
                      page = 1
                      docs = paginator.page(page)
                  except EmptyPage:
                      page = 1
                      docs = paginator.page(paginator.num_pages)

                  try:
                      docs_rel = paginator2.page(page)
                  except PageNotAnInteger:
                      docs_rel = paginator2.page(1)
                  except EmptyPage:
                      docs_rel = []

                  if docs:
                    docs.object_list = DocumentData.objects.filter(idd__in=[engine.index.get_doc_item(d).id for d in docs],source=source_type)
                  if docs_rel:
                    docs_rel.object_list = DocumentData.objects.filter(idd__in=[d for d in docs_rel],source=source_type)

                  context['documents'] = docs
                  context['documents_relevant'] = docs_rel
                  context['result_config'] = str(engine)
                  context['query_text'] = query_text
                  context['page'] = page
                  context['total_time'] = ("%.2f") % diff_in_seconds

                  query_request = QueryRequest()
                  query_request.text = query_text
                  query_request.query_processor = q_pro_type
                  query_request.search = search_type
                  query_request.time_request = diff_in_seconds
                  query_request.free_search = free_search
                  query_request.source = SourceType.objects.filter(slug=source_select,enable=True).first()
                  query_request.page = page
                  query_request.save()

                  #messages.add_message(self.request, INFO, )
            else:
                # Favor preencher as informações
                messages.add_message(self.request, ERROR, _('Please fill out the information'))
        except(Exception) as e:
            traceback.print_exc(file=sys.stdout)
            messages.add_message(self.request, ERROR, str(e))

        # Config

        self.request.session['source_select'] = source_select
        self.request.session['query_processor_select'] = query_processor_select
        self.request.session['search_model_select'] = search_model_select
        self.request.session['free_search'] = 'on' if free_search else ''


        session2context(context, self.request.session)
        return context



class DocumentView(TemplateView):
    template_name = 'document.html'

    def get_context_data(self, **kwargs):
        context = super(DocumentView, self).get_context_data(**kwargs)

        source_select = kwargs['source_select'] if 'source_select' in kwargs.keys() and \
                                                   kwargs['source_select'] else None
        doc_id = kwargs['doc_id'] if 'doc_id' in kwargs.keys() and \
                                               kwargs['doc_id'] else None

        try:
            if(source_select):
                  src_type = SourceType.objects.filter(slug=source_select).first()
                  #source = get_class(src_type.instance)(path=os.path.join(BASE_DIR, src_type.path))

                  context['doc'] = DocumentData.objects.filter(idd=doc_id,source=src_type).first() #source.read_doc(int(doc_id))
                  context['source_name'] = src_type.name

        except(Exception) as e:
            traceback.print_exc(file=sys.stdout)
            messages.add_message(self.request, ERROR, str(e))

        return context



def session2context(context,session):
    for k in session.keys():
        context[k] = session[k]


SOURCES_LIST = dict()

def ready():

    for s in SourceType.objects.filter(enable=True):
        source = get_class(s.instance)(path=os.path.join(BASE_DIR, s.path))
        #[d for d in source.read_docs()]
        source.read_querys()
        source.get_preprocessor().get_representation_docs()
        source.get_preprocessor().get_representation_query()

        SOURCES_LIST[s.slug] = source

    #print(SOURCES_LIST)
    #print("Init...")

ready()