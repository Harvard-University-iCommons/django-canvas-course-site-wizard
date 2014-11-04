from django.conf.urls import patterns, url

from .views import CanvasCourseSiteCreateView, CanvasCourseSiteStatusView, error_view

urlpatterns = patterns(
    '',
    url(r'^courses/(?P<pk>\d+)/create$', CanvasCourseSiteCreateView.as_view(), name='ccsw-create'),
    url(r'^status/(?P<pk>\d+)$', CanvasCourseSiteStatusView.as_view(), name='ccsw-status'),
    # CBV
    # url(r'^test-error$', CanvasCourseSiteErrorView.as_view(), name='ccsw-error'),
    url(r'^test-error$', error_view),
)

#TODO: may need to use 'ccsw.views.error_view' format
handler500 = handler400 = error_view