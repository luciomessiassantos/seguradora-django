from django.urls import path
from .views import *

urlpatterns = [
    path('', HeroPage.as_view(), name='hero'),
    path('policy_search/', SearchPolicyAjaxView.as_view(), name='policy_search'),
]
