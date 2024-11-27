from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_contact, name='create_contact'),
]
urlpatterns += [
    path('', views.index, name='index'),
    path('contacts/', views.contacts_list, name='contacts_list'),
    path('tags/', views.tag_list, name='tag_list'),
    path('tags/add/', views.add_tag, name='add_tag'),
    path('search/', views.search_contacts, name='search_contacts'),
    path('export/', views.export_contacts, name='export_contacts'),
    path('import/', views.import_contacts, name='import_contacts'),

]