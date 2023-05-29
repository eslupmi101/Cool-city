from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreateModel

User = get_user_model()


class Group(CreateModel):
    title = models.CharField(
        max_length=200,
        verbose_name='Название группы',
        help_text='Введите название группы'
    )
    description = models.TextField(verbose_name='Описание группы',
                                   help_text='Введите описание группы')
    slug = models.SlugField(unique=True, verbose_name='Адрес группы')

    class Meta:
        verbose_name = ' Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.title


class Post(CreateModel):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Введите текст поста'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        related_name='group',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='posts/',
        blank=True,
        help_text='Загрузить изображение'
    )
    likes = models.IntegerField(
        verbose_name='Лайки',
        blank=True,
        null=True,
        default=0
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:15]


class Comment(CreateModel):
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Текст вашего комментария'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text[:15]


class Follow(CreateModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('author',)
        constraints = (
            models.UniqueConstraint(
                fields=['author', 'user'], name='unique_follow'
            ),
        )


class Like(CreateModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='who_liked',
        verbose_name='Поставил лайк'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='post',
        verbose_name='Пост'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('post',)
        constraints = (
            models.UniqueConstraint(
                fields=['post', 'user'], name='unique_follow'
            ),
        )
