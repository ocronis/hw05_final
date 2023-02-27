from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.some_user = User.objects.create_user(username='IvanFakov')
        cls.author_user = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовый текст',
        )
        cls.post = Post.objects.create(
            author=cls.author_user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.some_user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author_user)
        cache.clear()

    def test_urls_exists_at_desired_location(self):
        """Страницы доступна любому пользователю."""
        reverses = [
            reverse('posts:index'),
            reverse('posts:group_slug', kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.author_user.username}),
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
        ]
        for reverse_name in reverses:
            with self.subTest(url=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page(self):
        """Страница /unexisting_page/ не существует."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_url_exists_at_desired_location_authorized(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get(reverse('posts:create'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_url_exists_at_desired_location_author(self):
        """Страница /.../edit/ доступна только автору."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.authorized_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_slug',
                    kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.author_user.username}
                    ): 'posts/profile.html',
            (reverse('posts:post_detail', kwargs={'post_id': self.post.id})
             ): 'posts/post_detail.html',
            reverse('posts:create'): 'posts/create_post.html',
            (reverse('posts:post_edit', kwargs={'post_id': self.post.id})
             ): 'posts/create_post.html',
        }
        for url, template in url_templates_names.items():
            with self.subTest(url=url):
                response = self.authorized_author.get(url)
                self.assertTemplateUsed(response, template)
