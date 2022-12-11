from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):

    post = None
    user = None
    group = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='группа для теста',
            slug='test_slug',
        )
        cls.user = User.objects.create(
            username='user_test'
        )
        cls.post = Post.objects.create(
            text='текст',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):

        cache.clear()
        self.guest_client = Client()
        self.user = PostURLTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.url_only_authorized = ['/create/', '/posts/1/edit/']
        self.url_non_existent = ['/non_existent_page/']
        self.url_full_list = [
            '/',
            '/group/test_slug/',
            '/create/',
            '/posts/1/',
            '/posts/1/edit/',
            '/profile/user_test/',
            '/non_existent_page/',
        ]

    def test_url_for_guest(self):
        """Тест: проверка доступности страниц для гостя """
        for i_adress in self.url_full_list:
            with self.subTest(adress=i_adress):
                response = self.guest_client.get(i_adress)

                if i_adress in self.url_only_authorized:
                    self.assertEqual(
                        response.status_code,
                        HTTPStatus.FOUND,
                        f'Для гостя страница {i_adress} недоступена'
                    )
                elif i_adress in self.url_non_existent:
                    self.assertEqual(
                        response.status_code,
                        HTTPStatus.NOT_FOUND,
                        f'Для гостя проверка доступа к '
                        f'несуществующей странице {i_adress} провалена'
                    )
                else:
                    self.assertEqual(
                        response.status_code,
                        HTTPStatus.OK,
                        f'Для гостя страница {i_adress} недоступена'
                    )

    def test_url_for_authorized(self):
        """Тест: проверка доступности страниц для авторизованного """
        for i_adress in self.url_full_list:
            with self.subTest(adress=i_adress):
                response = self.authorized_client.get(i_adress)
                if i_adress in self.url_non_existent:
                    self.assertEqual(
                        response.status_code,
                        HTTPStatus.NOT_FOUND,
                        f'Для авторизованного проверка доступа к'
                        f' несуществующей странице {i_adress} провалена'
                    )
                else:
                    self.assertEqual(
                        response.status_code,
                        HTTPStatus.OK,
                        f'Для авторизованного страница {i_adress} недоступена'
                    )

    def test_authorized_redirects(self):
        """Тест: редиректа у авторизованного пользователя — не автора"""
        author = PostURLTests.post.author
        if author != self.user:
            response = self.authorized_client.get(
                '/posts/1/edit/',
                follow=True
            )
            self.assertRedirects(response, '/posts/1/')

    def test_guest_redirects(self):
        """Тест: редиректа у гостя"""
        url = '/posts/1/edit/'
        response = self.guest_client.get(
            url,
            follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=' + url)

    def test_url_template_app_posts(self):
        """Тест: URL-адреса и шаблона."""
        templates_url = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/posts/1/edit/': 'posts/post_create.html',
            '/posts/1/': 'posts/post_detail.html',
            '/profile/user_test/': 'posts/profile.html',
            '/create/': 'posts/post_create.html',
        }
        for i_adress, i_template in templates_url.items():
            with self.subTest(adress=i_adress):
                if i_adress in self.url_only_authorized:
                    response = self.authorized_client.get(i_adress)
                    self.assertTemplateUsed(
                        response,
                        i_template,
                        f'Для авторизованного пользователя по адресу'
                        f' {i_adress} в шаблоне {i_template} ошибка.'
                    )
                else:
                    response = self.guest_client.get(i_adress)
                    self.assertTemplateUsed(
                        response,
                        i_template,
                        f'Для гостя по адресу {i_adress} '
                        f'в шаблоне {i_template} ошибка.'
                    )
