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
        count_before_paginator = self.get_count_paginator_group_list()
        count_before_db = Post.objects.count()
        self.assertEqual(count_before_db, count_before_paginator,
                         'подсчет количества записей '
                         'до вызова post - провален')

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

        self.assertEqual(Post.objects.count(), count_before_db + 1)
        post = Post.objects.latest('id')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.post_author)
        self.assertEqual(post.group_id, form_data['group'])
        count_after_paginator = self.get_count_paginator_group_list()
        count_after_db = Post.objects.count()
        self.assertEqual(count_after_db, count_after_paginator,
                         'подсчет количества записей после '
                         'post - провален')

    def test_authorized_user_edit_post(self):
        """Проверка редактирования записи авторизированным автором."""
        post_created = Post.objects.create(
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
            reverse("posts:post_edit", args=(post_created.id,)),
            data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post_created.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post_edited = Post.objects.get(pk=post_created.id)
        self.assertEqual(post_edited.text, form_data['text'])
        self.assertEqual(post_edited.author, self.post_author)
        self.assertEqual(post_edited.pub_date, post_created.pub_date)
        self.assertEqual(post_edited.group_id, form_data['group'])

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

    def test_form_post_edit_authorised_client_nonauthor(self):
        '''Проверяем, что при авторизованном не авторе
        форма не редактирует запись'''
        post_for_edit = Post.objects.create(
            author=PostFormTests.post_author,
            text='Тестовый пост 2',
            group=self.group,
        )
        id_post = post_for_edit.id
        form_data = {
            'text': 'New',
            'group': self.group_new.id,
        }
        self.user2 = User.objects.create_user(username='Non_post_writer')
        self.authorised_client2 = Client()
        self.authorised_client2.force_login(self.user2)
        response = self.authorised_client2.post(
            reverse('posts:post_edit', kwargs={'post_id': id_post}),
            data=form_data,
        )
        post_edited = Post.objects.get(pk=id_post)
        self.assertNotEqual(post_edited.text, form_data['text'])
        self.assertEqual(post_edited.author, self.post_author)
        self.assertEqual(post_edited.pub_date, post_for_edit.pub_date)
        self.assertNotEqual(post_edited.group_id, form_data['group'])
        self.assertRedirects(
            response, f'/posts/{id_post}/'
        )

    def test_edit_post_anonim(self):
        """Проверка при запросе неавторизованного пользователя
        пост не будет отредактирован."""
        post_for_edit = Post.objects.create(
            author=PostFormTests.post_author,
            text='Тестовый пост 2',
            group=self.group,
        )
        id_post = post_for_edit.id
        form_data = {
            'text': 'New',
            'group': self.group_new.id,
        }
        response = self.guest_user.post(
            reverse('posts:post_edit', kwargs={'post_id': id_post}),
            data=form_data,
        )
        post_edited = Post.objects.get(pk=id_post)
        self.assertNotEqual(post_edited.text, form_data['text'])
        self.assertEqual(post_edited.author, self.post_author)
        self.assertEqual(post_edited.pub_date, post_for_edit.pub_date)
        self.assertNotEqual(post_edited.group_id, form_data['group'])
        self.assertRedirects(
            response, reverse("login") + "?next=" + reverse(
                "posts:post_edit", kwargs={"post_id": id_post})
        )

    def test_authorized_user_create_post_without_group(self):
        """Проверка создания записи авторизированным клиентом без группы."""
        count_before_paginator_group = self.get_count_paginator_group_list()
        count_before_db = Post.objects.count()
        self.assertEqual(
            count_before_db,
            count_before_paginator_group,
            "подсчет количества записей " "до вызова post - провален",
        )

        form_data = {
            'text': 'Текст поста',
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

        self.assertEqual(Post.objects.count(), count_before_db + 1)
        post = Post.objects.latest('id')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.post_author)
        count_after_paginator_group = self.get_count_paginator_group_list()
        count_after_db = Post.objects.count()
        self.assertNotEqual(count_after_db, count_after_paginator_group,
                            'подсчет количества записей после '
                            'post - провален')
