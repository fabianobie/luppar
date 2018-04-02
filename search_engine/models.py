# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db.models import *
from django.contrib.contenttypes.models import ContentType
from django.db import models as models
from django_extensions.db import fields as extension_fields

from search_engine.fulltext import SearchManager


class EngineBase(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    instance = models.CharField(max_length=100)
    parameters = models.TextField(max_length=200,blank=True,null=True)
    enable = models.NullBooleanField(default=False, blank=True, null=True)


class SourceType(EngineBase):
    path = models.CharField(max_length=200,blank=True,null=True)
    preprocessor = models.CharField(max_length=200,blank=True,null=True)


    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        return u'%s' % self.slug


class QueryProcessorType(EngineBase):
    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        return u'%s' % self.slug


class SearchType(EngineBase):
    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        return u'%s' % self.slug


class ContextType(EngineBase):
    class Meta:
        ordering = ('-created',)


class QueryRequest(models.Model):

    # Fields
    created = models.DateTimeField(auto_now_add=True, editable=False)
    text = models.TextField(max_length=1000)

    # Relationship Fields
    source = models.ForeignKey(SourceType,models.DO_NOTHING, null=True, blank=True)
    query_processor = models.ForeignKey(QueryProcessorType,models.DO_NOTHING,null=True, blank=True)
    search = models.ForeignKey(SearchType,models.DO_NOTHING,null=True, blank=True)
    context = models.ForeignKey(ContentType,models.DO_NOTHING,null=True, blank=True)
    time_request = models.FloatField(null=True, blank=True)
    free_search = models.NullBooleanField()
    page = models.IntegerField(null=True,blank=True)

    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        return u'%s' % self.pk


class DocumentData(models.Model):
    idd = models.BigIntegerField()
    source = models.ForeignKey(SourceType, models.DO_NOTHING, null=True, blank=True)
    title = models.CharField(max_length=1000, null=True, blank=True)
    description = models.CharField(max_length=2000, null=True, blank=True)
    name = models.CharField(max_length=255,null=True,blank=True)
    code = models.CharField(max_length=100,null=True,blank=True)
    prev_text = models.CharField(max_length=255,null=True,blank=True)
    text = models.TextField(null=True,blank=True)
    path = models.CharField(max_length=255,null=True,blank=True)


    # Enable full-text search support for text fields.
    objects = SearchManager(['name','text'])

    class Meta:
        ordering = ('-id',)

    def __unicode__(self):
        return u'%s' % self.name

class QueryData(models.Model):
    idq = models.BigIntegerField()
    source = models.ForeignKey(SourceType, models.DO_NOTHING, null=True, blank=True)
    prev_text = models.CharField(max_length=255,null=True,blank=True)
    text = models.TextField(null=True,blank=True)
    relevant_docs = models.ManyToManyField(DocumentData)

    # Enable full-text search support for text fields.
    objects = SearchManager(['text'])

    class Meta:
        ordering = ('-id',)

    def __unicode__(self):
        return u'%s' % self.text

