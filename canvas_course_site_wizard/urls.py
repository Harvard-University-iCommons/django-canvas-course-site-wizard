from django.conf.urls import patterns, url

from .views import (CanvasCourseSiteCreateView, CanvasCourseSiteStatusView, CanvasBulkCreateStatusView)

urlpatterns = patterns(
    '',
    url(r'^courses/(?P<pk>\d+)/create$', CanvasCourseSiteCreateView.as_view(), name='ccsw-create'),
    url(r'^status/(?P<pk>\d+)$', CanvasCourseSiteStatusView.as_view(), name='ccsw-status'),
    url(r'^bulk_create/(?P<pk>\d+)$', CanvasBulkCreateStatusView.as_view(), name='ccsw-bulk-create')
)
