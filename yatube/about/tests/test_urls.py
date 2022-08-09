import http

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Тестируем коды ответа, возвращаемые страницами"""

        addresses_response_codes = {
            '/about/author/': http.HTTPStatus.OK,
            '/about/tech/': http.HTTPStatus.OK
        }
        for address, response_code in addresses_response_codes.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, response_code)

    def test_about_url_uses_correct_template(self):
        """Тестируем используемые страницами шаблоны"""

        templates_url_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
