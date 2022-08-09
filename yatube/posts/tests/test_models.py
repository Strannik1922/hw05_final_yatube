from django.test import TestCase
from posts.models import Group, Post, User


class PostModelTest(TestCase):
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
            author=cls.user,
            text='Тестовый пост',
        )

    def test_value_title_field_group(self):
        """Проверяем, что у моделей корректно работает __str__."""
        task = PostModelTest.group
        expected_value = task.title
        self.assertEqual(expected_value, str(task))

    def test_value_text_field_post(self):
        """Проверяем, что у моделей корректно работает __str__."""
        task = PostModelTest.post
        expected_value = task.text
        self.assertEqual(expected_value, str(task))

    def test_post_verbose_name(self):
        """verbose_name в полях модели Post совпадает с ожидаемым"""

        task = PostModelTest.post
        field_verbose = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }
        for field, expected_value in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    task._meta.get_field(field).verbose_name, expected_value)

    def test_post_help_text(self):
        """help_text в полях модели Post совпадает с ожидаемым"""

        task = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    task._meta.get_field(field).help_text, expected_value)
