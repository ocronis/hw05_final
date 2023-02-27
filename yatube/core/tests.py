from django.test import TestCase


class CoreURLTests(TestCase):

    def test_unexisting_page(self):
        """Страница /unexisting_page/ использует соответствующий шаблон."""
        self.assertTemplateUsed(self.client.get('/unexisting_page/'),
                                'core/404.html')
