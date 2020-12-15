from django.contrib import admin

from repository.models import Repository, FileType, FileExt, RepoSize


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):

    list_display = ['name', 'path']
    search_fields = ['name']


class FileExtInline(admin.TabularInline):
    model = FileExt
    extra = 0


@admin.register(FileType)
class FileTypeAdmin(admin.ModelAdmin):

    list_display = ['name']
    search_fields = ['name']
    inlines = [FileExtInline]


@admin.register(FileExt)
class FileExtAdmin(admin.ModelAdmin):

    list_display = ['name', 'type']
    list_filter = ['type']
    search_fields = ['name']

@admin.register(RepoSize)
class RepoSizeAdmin(admin.ModelAdmin):

    list_display = ['timestamp', 'repo', 'size']
    list_filter = ['repo']
    search_fields = ['repo']
