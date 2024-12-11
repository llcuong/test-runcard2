from django.urls import re_path as url
from runcard.views import barcodepage, search_for_runcard, barcodepage2

urlpatterns = [
    url(r'search', search_for_runcard, name='search'),
    url(r'barcodepage2/', barcodepage2, name='barcodepage2'),
    url(r'', barcodepage, name='barcodepage'),
]