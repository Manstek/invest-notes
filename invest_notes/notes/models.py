from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Label(models.Model):
    author = models.ManyToManyField(User, verbose_name="авторы меток")

    title = models.CharField(max_length=16, verbose_name='Метка',
                             help_text='название метки')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Метка пользователя {self.author.username} : {self.title}'


class Note(models.Model):
    author = models.ForeignKey(User, related_name='notes',
                               on_delete=models.CASCADE)
    labels = models.ManyToManyField(Label)

    text = models.TextField(verbose_name='Текст', help_text='Текст заметки')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (f'Заметка от пользователя {self.author.username}'
                f': {self.text[:10]}...')
