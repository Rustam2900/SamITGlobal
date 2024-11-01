from modeltranslation.translator import TranslationOptions, register
from bot import models


@register(models.CustomUser)
class CustomUserTranslation(TranslationOptions):
    fields = ('full_name', 'username')


@register(models.Course)
class CustomUserTranslation(TranslationOptions):
    fields = ('title', 'description', 'course_duration')
