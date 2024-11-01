from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from bot.models import CustomUser, Course


@admin.register(CustomUser)
class WhyUsAdmin(TranslationAdmin):
    list_display = ('id', 'username', 'phone_number')
    list_display_links = ('id', 'username', 'phone_number')
    search_fields = ('username', 'phone_number')

@admin.register(Course)
class WhyUsAdmin(TranslationAdmin):
    list_display = ('id', 'title', 'price', 'course_duration')
    list_display_links = ('id', 'title', 'price', 'course_duration')
    search_fields = ('id', 'title')
