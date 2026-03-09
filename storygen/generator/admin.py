from django.contrib import admin
from .models import ImageStory


@admin.register(ImageStory)
class ImageStoryAdmin(admin.ModelAdmin):
    """Admin configuration for ImageStory model."""

    list_display = ('id', 'language', 'created_at')
    list_filter = ('language', 'created_at')
    search_fields = ('story',)
    readonly_fields = ('created_at',)