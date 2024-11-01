from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password
from bot.validators import phone_number_validator


class Course(models.Model):
    title = models.CharField(_("title"), max_length=200)
    description = models.TextField(_("description"))
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    course_duration = models.CharField(_("course_duration"), max_length=100, null=True, blank=True)

    def __str__(self):
        return self.title


class CustomUser(models.Model):
    full_name = models.CharField(_("full name"), blank=True, max_length=255)
    username = models.CharField(_("username"), blank=True, max_length=255, null=True)
    phone_number = models.CharField(_("phone number"), blank=True, unique=True, validators=[phone_number_validator],
                                    max_length=20)
    user_lang = models.CharField(_("user language"), blank=True, null=True, max_length=10)
    telegram_id = models.CharField(_("telegram id"), blank=True, null=True, max_length=255, unique=True)
    tg_username = models.CharField(_("telegram username"), blank=True, null=True, max_length=255, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return self.full_name
