from django.contrib import admin

from repository.models import Repository


@admin.register(Repository)
class MenuAdmin(admin.ModelAdmin):

    list_display = ['name', 'path']
    search_fields = ['name']