import http

from http import HTTPStatus

from django.test import Client, TestCase
from posts.models import Group, Post, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.non_author = User.objects.create_user(username='Ivan')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.non_author_client = Client()
        self.non_author_client.force_login(self.non_author)

    def test_all_urls_use_correct_template(self):
        """Тестируем используемые страницами шаблоны.Для этого используем
        учётку автора поста, чтобы проверить сразу все страницы
        """

        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            '/follow/': 'posts/follow.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_all_urls_return_correct_response(self):
        """Тестируем коды ответа, возвращаемые страницами"""

        addresses_response_codes = {
            '/': http.HTTPStatus.OK,
            f'/group/{self.group.slug}/': http.HTTPStatus.OK,
            f'/posts/{self.post.id}/': http.HTTPStatus.OK,
            f'/posts/{self.post.id}/edit/': http.HTTPStatus.OK,
            '/create/': http.HTTPStatus.OK,
            f'/profile/{self.user.username}/': http.HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            '/follow/': http.HTTPStatus.OK,
            f'/posts/{self.post.id}/comment/': http.HTTPStatus.FOUND,
            f'/profile/{self.user.username}/follow':
                http.HTTPStatus.MOVED_PERMANENTLY,
            f'/profile/{self.user.username}/unfollow':
                http.HTTPStatus.MOVED_PERMANENTLY
        }
        for address, response_code in addresses_response_codes.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, response_code)

    def test_post_edit_correct_responses(self):
        """Тестируем, что страница редактирования поста
        корректно работает для неавторизованного пользователя
        """

        different_templates_of_url = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': http.HTTPStatus.OK,
            f'/posts/{self.post.id}/': http.HTTPStatus.OK,
            '/create/': http.HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND
        }
        for address, response_code in (
            different_templates_of_url.items()
        ):
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, response_code)

    def test_post_edit_correct_responses(self):
        """Тестируем, что страница редактирования поста
        корректно работает для не для автора поста
        """

        with self.subTest(address=f'/posts/str{self.post.id}/edit/'):
            response = self.non_author_client.get(
                f'/posts/{self.post.id}/edit/',
                follow=True
            )
            self.assertTemplateUsed(response, 'posts/post_detail.html')
