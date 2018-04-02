"""luppar URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
import os
from django.conf.urls import include, url
from django.contrib import admin
#from django.core.cache import cache

from luppar.settings import SOURCES_LIST
from .settings import BASE_DIR

from engine.util import get_class
from search_engine import views
from search_engine.models import SourceType
from django.views.decorators.cache import cache_page
from search_engine.views import IndexView, SearchView, DocumentView, AboutView, ResultView

urlpatterns = [
    url(r'^$', cache_page(0)(IndexView.as_view()), name='index'),
    url(r'^about$', cache_page(0)(AboutView.as_view()), name='about'),
    url(r'^result$', cache_page(0)(ResultView.as_view()), name='result'),
    url(r'^search$', cache_page(60*240)(SearchView.as_view()), name='search'),
    url(r'^query_preview$', cache_page(0)(views.query_preview), name='query_preview'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^document/(?P<source_select>\w+)/(?P<doc_id>\w+)$', DocumentView.as_view(), name='document'),
    url('i18n/', include('django.conf.urls.i18n')),
]
