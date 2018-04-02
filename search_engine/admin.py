# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django import forms
from .models import SourceType, QueryProcessorType, SearchType, ContextType, QueryRequest

class SourceTypeAdminForm(forms.ModelForm):

    class Meta:
        model = SourceType
        fields = '__all__'


class SourceTypeAdmin(admin.ModelAdmin):
    form = SourceTypeAdminForm
    list_display = ['name', 'instance', 'parameters','path']
    readonly_fields = ['slug', 'created', 'last_updated']

admin.site.register(SourceType, SourceTypeAdmin)


class QueryProcessorTypeAdminForm(forms.ModelForm):

    class Meta:
        model = QueryProcessorType
        fields = '__all__'


class QueryProcessorTypeAdmin(admin.ModelAdmin):
    form = QueryProcessorTypeAdminForm
    list_display = ['name', 'instance', 'parameters']
    readonly_fields = ['slug', 'created', 'last_updated']

admin.site.register(QueryProcessorType, QueryProcessorTypeAdmin)


class SearchTypeAdminForm(forms.ModelForm):

    class Meta:
        model = SearchType
        fields = '__all__'


class SearchTypeAdmin(admin.ModelAdmin):
    form = SearchTypeAdminForm
    list_display = ['name', 'instance', 'parameters']
    readonly_fields = ['slug', 'created', 'last_updated']

admin.site.register(SearchType, SearchTypeAdmin)


class ContextTypeAdminForm(forms.ModelForm):

    class Meta:
        model = ContextType
        fields = '__all__'


class ContextTypeAdmin(admin.ModelAdmin):
    form = ContextTypeAdminForm
    list_display = ['name','instance', 'parameters']
    readonly_fields = ['slug', 'created', 'last_updated']

admin.site.register(ContextType, ContextTypeAdmin)


class QueryRequestAdminForm(forms.ModelForm):

    class Meta:
        model = QueryRequest
        fields = '__all__'


class QueryRequestAdmin(admin.ModelAdmin):
    form = QueryRequestAdminForm
    list_display = ['created', 'text']
    readonly_fields = ['created', 'text']

admin.site.register(QueryRequest, QueryRequestAdmin)
