from django.test import TestCase, Client
from http import HTTPStatus


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_urls_exists_at_desired_location(self):
        """Страницы доступна любому пользователю."""
        url_names = [
            '/about/author/',
            '/about/tech/',
        ]
        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for url, template in url_templates_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
