from django.urls import path

from repository import views

app_name = 'repository'

urlpatterns = [
    path('list/', views.RepositoryList.as_view(), name='list'),
    path('create/', views.RepositoryCreate.as_view(), name='create'),
    path('update/<int:pk>/', views.RepositoryUpdate.as_view(), name='update'),
    path('snapshots/<int:pk>/', views.RepositorySnapshots.as_view(), name='snapshots'),
    path('browse/<int:pk>/<str:view>/', views.FileBrowse.as_view(), name='browse'),
    path('restore/<int:pk>/<str:view>/', views.RestoreView.as_view(), name='restore'),
    path('backup/<int:pk>/', views.BackupView.as_view(), name='backup'),
    path('newbackup/<int:pk>/', views.NewBackupView.as_view(), name='newbackup'),
    path('journal/', views.JournalView.as_view(), name='journal'),
]