from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.

class Note(models.Model):
    title = models.CharField(max_length=255, blank=False, null=False)
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notes')
    folder = models.ForeignKey('Folder', on_delete=models.SET_NULL, null=True, blank=True, related_name='notes')
    
    class Meta:
        ordering = ['-created_at']  # Сортировка по дате создания, от новых к старым

    def __str__(self):
        return self.title


class Folder(models.Model):
    name = models.CharField(max_length=255, unique=True)  # Название папки, уникальное для пользователя
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='folders')  # Связь с пользователем
    
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания папки
    updated_at = models.DateTimeField(auto_now=True)  # Дата последнего обновления
    
    class Meta:
        ordering = ['-updated_at']  # Сортировка папок по обновлению

    def __str__(self):
        return self.name


class User(AbstractUser):
    telegram_id = models.BigIntegerField(unique=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='notes_user_groups',  # Измените related_name
        blank=True,
        help_text='The groups this user belongs to.'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='notes_user_permissions',  # Измените related_name
        blank=True,
        help_text='Sеpecific permissions for this user.'
    )