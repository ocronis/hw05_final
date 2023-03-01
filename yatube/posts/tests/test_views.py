import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post
from ..views import NUMBER_OF_POSTS_ON_PAGE

User = get_user_model()

NUMBER_OF_TEST_POSTS = 15
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='IvanFakov')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовый текст',
        )
        cls.bad_group = Group.objects.create(
            title='Плохой заголовок',
            slug='bad-slug',
            description='Плохой текст',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def equality_check(self, context):
        self.assertEqual(context.text, self.post.text)
        self.assertEqual(context.author, self.user)
        self.assertEqual(context.group, self.group)
        self.assertEqual(context.id, self.post.id)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:group_slug', kwargs={'slug': self.group.slug})
             ): 'posts/group_list.html',
            (reverse('posts:profile', kwargs={'username': self.user.username})
             ): 'posts/profile.html',
            (reverse('posts:post_detail', kwargs={'post_id': self.post.id})
             ): 'posts/post_detail.html',
            (reverse('posts:post_edit', kwargs={'post_id': self.post.id})
             ): 'posts/create_post.html',
            reverse('posts:create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_list_pages_show_correct_context(self):
        """Шаблоны со списками постов сформированы с правильным контекстом."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:group_slug', kwargs={'slug': self.group.slug})
             ): 'posts/group_list.html',
            (reverse('posts:profile', kwargs={'username': self.user.username})
             ): 'posts/profile.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                self.equality_check(first_object)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.client.get(reverse('posts:post_detail',
                                           kwargs={'post_id': self.post.id}))
        post = response.context['post']
        self.equality_check(post)

    def test_form_pages_show_correct_context(self):
        """Шаблоны с формами сформированы с правильным контекстом."""
        templates_page_names = {
            (reverse('posts:post_edit', kwargs={'post_id': self.post.id})
             ): 'posts/create_post.html',
            reverse('posts:create'): 'posts/create_post.html',
        }
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context['form'].fields[value]
                        self.assertIsInstance(form_field, expected)

    def test_pages_show_img(self):
        """Картинка тестового поста отображается на необходимых страницах."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': uploaded,
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )

        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:group_slug', kwargs={'slug': self.group.slug})
             ): 'posts/group_list.html',
            (reverse('posts:profile', kwargs={'username': self.user.username})
             ): 'posts/profile.html',
            (reverse('posts:post_detail', kwargs={'post_id': self.post.id})
             ): 'posts/post_detail.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.client.get(reverse_name)
                self.assertContains(response, '<img')

    def test_post_create(self):
        self.post = Post.objects.create(
            author=self.user,
            text='Новый пост',
            group=self.group
        )
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:group_slug', kwargs={'slug': self.group.slug})
             ): 'posts/group_list.html',
            (reverse('posts:profile', kwargs={'username': self.user.username})
             ): 'posts/profile.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                self.equality_check(response.context['page_obj'][0])

        response = self.client.get(reverse_name)
        first_object = response.context['page_obj'][0]
        self.assertNotEqual(first_object.group, self.bad_group)


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='IvanFakov')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовый текст',
        )
        i = 1
        while i <= NUMBER_OF_TEST_POSTS:
            cls.post = Post.objects.create(
                author=cls.user,
                text='Тестовый пост' + str(i),
                group=cls.group
            )
            i += 1

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_page_contains_correct_number_of_records(self):
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:group_slug', kwargs={'slug': self.group.slug})
             ): 'posts/group_list.html',
            (reverse('posts:profile', kwargs={'username': self.user.username})
             ): 'posts/profile.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response_first_page = self.guest_client.get(reverse_name)
                response_second_page = (
                    self.guest_client.get(reverse('posts:index') + '?page=2'))
                self.assertEqual(len(response_first_page.context['page_obj']),
                                 NUMBER_OF_POSTS_ON_PAGE)
                self.assertEqual(len(response_second_page.context['page_obj']),
                                 (NUMBER_OF_TEST_POSTS
                                  - NUMBER_OF_POSTS_ON_PAGE))
                cache.clear()


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='IvanFakov')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_create_post(self):
        """Комментирование доступно только авторизированным пользователям."""
        template = reverse('posts:post_detail',
                           kwargs={'post_id': self.post.id})
        response = self.authorized_client.get(template)
        self.assertContains(response, 'comment')
        response = self.client.get(template)
        self.assertNotContains(response, 'comment')


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='IvanFakov')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_cache(self):
        """Кэширование работает."""
        content_start = self.client.get(reverse('posts:index')).content
        Post.objects.filter(author=self.user).delete()
        self.assertFalse(Post.objects.filter(author=self.user).exists())
        content_cache = self.client.get(reverse('posts:index')).content
        self.assertEqual(content_start, content_cache)
        cache.clear()
        content_end = self.client.get(reverse('posts:index')).content
        self.assertNotEqual(content_start, content_end)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username='IvanFakov')
        cls.follower_user = User.objects.create_user(username='VasyaPupkin')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.follower_user)
        cache.clear()

    def test_follow_create(self):
        """Авторизованный пользователь может подписываться на других
        пользователей."""
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author_user.username}))
        self.assertTrue(
            Follow.objects.filter(user=self.follower_user,
                                  author=self.author_user).exists())

    def test_follow_delete(self):
        """Авторизованный пользователь может удалять других
        пользователей из подписок."""
        Follow.objects.create(user=self.follower_user, author=self.author_user)
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author_user.username}))
        self.assertFalse(
            Follow.objects.filter(user=self.follower_user,
                                  author=self.author_user).exists())

    def test_follow_post(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан."""
        post = Post.objects.create(
            author=self.author_user,
            text='Тестовый пост',
        )
        self.assertNotContains(
            self.authorized_client.get(reverse('posts:follow_index')),
            post.text)
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author_user.username}))
        self.assertContains(
            self.authorized_client.get(reverse('posts:follow_index')),
            post.text)
