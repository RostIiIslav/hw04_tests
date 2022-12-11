from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            text='Тестовый текст больше 15 символов для проверки...',
            author=cls.user,
        )

    def test_post_str(self):
        """Тест: __str__ у post."""
        self.assertEqual(self.post.text[:15], str(self.post))


class GroupModelTest(TestCase):
    user = None
    post = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст больше 15 символов для проверки...',
            author=cls.user,
        )

    def test_group_str(self):
        """Тест: __str__ у group."""
        self.assertEqual(self.group.title, str(self.group))

    def test_verbose_name(self):
        post = GroupModelTest.post
        field_verboses = {
            'text': 'Текст нового поста',
            'author': 'Автор',
            'group': 'Группа'
        }
        for i_field, expected_value in field_verboses.items():
            with self.subTest(field=i_field):
                self.assertEqual(
                    post._meta.get_field(i_field).verbose_name,
                    expected_value)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = GroupModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)