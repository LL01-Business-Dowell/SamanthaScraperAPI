from django.urls import path
from . import views

urlpatterns = [
    path('process/', views.CreateProcessView.as_view(), name= 'process'),

]