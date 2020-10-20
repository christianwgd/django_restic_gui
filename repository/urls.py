from django.urls import path

from repository import views

app_name = 'repository'

urlpatterns = [
    path('list/', views.RepositoryList.as_view(), name='list'),
    path('snapshots/<int:pk>/', views.RepositorySnapshots.as_view(), name='snapshots'),
    path('browse/<int:pk>/', views.FileBrowse.as_view(), name='browse'),
]