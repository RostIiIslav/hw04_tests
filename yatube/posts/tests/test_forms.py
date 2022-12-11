from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_author = User.objects.create_user(
            username='post_author',
        )
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        cls.group_new = Group.objects.create(
            title='Тестовое название группы: Сериалы',
            slug='test_slug_new',
            description='Тестовое описание группы',
        )

    def setUp(self):
        self.guest_user = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.post_author)

    def get_count_paginator_group_list(self):
        group_response = self.authorized_user.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        return group_response.context['page_obj'].paginator.count

    def test_authorized_user_create_post(self):
        """Проверка создания записи авторизированным клиентом."""
        count_before = self.get_count_paginator_group_list()
        self.assertEqual(0, count_before,
                         'подсчет количества записей '
                         'до вызова post - провален')

        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id,
        }
        response = self.authorized_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.post_author.username})
        )

        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.latest('id')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.post_author)
        self.assertEqual(post.group_id, form_data['group'])
        count_after = self.get_count_paginator_group_list()
        self.assertEqual(1, count_after,
                         'подсчет количества записей после '
                         'post - провален')

    def test_authorized_user_edit_post(self):
        """Проверка редактирования записи авторизированным клиентом."""
        post = Post.objects.create(
            text='Текст поста для редактирования',
            author=self.post_author,
            group=self.group,
        )
        form_data = {
            'text': 'Отредактированный текст поста',
            'group': self.group_new.id,
        }
        prev_count_post = self.get_count_paginator_group_list()
        response = self.authorized_user.post(
           reverse(
        'posts:post_edit',
        args=(post.id,)),
        data=form_data,
        follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post = Post.objects.latest('id')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.post_author)
        self.assertEqual(post.group_id, form_data['group'])

        new_count_post = self.get_count_paginator_group_list()
        self.assertEqual(prev_count_post - 1, new_count_post,
                         'до редактирования названия группы поста постов '
                         f'было {prev_count_post}, стало {new_count_post} '
                         '- тест провален')

    def test_nonauthorized_user_create_post(self):
        """Проверка создания записи не авторизированным пользователем."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id,
        }
        response = self.guest_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        redirect = reverse('login') + '?next=' + reverse('posts:post_create')
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), posts_count)
