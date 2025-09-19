from django.db import models
from django.db.models import UniqueConstraint, functions
from django.contrib.auth import get_user_model

from .validators import validate_title


User = get_user_model()


class Label(models.Model):
    owner = models.ForeignKey(User, verbose_name="владелец метки",
                              on_delete=models.CASCADE)

    title = models.CharField(max_length=50, verbose_name='Метка',
                             help_text='название метки',
                             validators=[validate_title,])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'метка'
        verbose_name_plural = 'Метки'
        ordering = ('title',)
        default_related_name = 'labels'
        UniqueConstraint(fields=[functions.Lower('title'), 'owner'],
                         name='unique_label_per_user_case_insensitive')


class Note(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    labels = models.ManyToManyField(Label)

    text = models.TextField(verbose_name='Текст', help_text='Текст заметки')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'заметка'
        verbose_name_plural = 'Заметки'
        default_related_name = 'notes'

    def __str__(self):
        return (f'Заметка от пользователя {self.author.username}'
                f': {self.text[:10]}...')
