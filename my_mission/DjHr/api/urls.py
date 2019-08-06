from django.conf.urls import url, include
from .views import *

urlpatterns = [
    url(r'^get/refresh/(\d)/(\w)$', info_api),
    url(r'^post/(\d)/(\w)/(.*?)$', insert_info)
]