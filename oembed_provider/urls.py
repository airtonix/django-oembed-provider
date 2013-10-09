from django.conf.urls.defaults import patterns, url
from . import views

urlpatterns = patterns('',
                       url(r'^$', views.OembedSchemaView.as_view(), name='oembed_schema'),
                       url(r'^json/$', views.OembedResourceView.as_view(), name='oembed_json'),
                       # url(r'^consume/json/$', views.OembedConsumeJsonView.as_view(), name='oembed_consume_json'),
                       )
