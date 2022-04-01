from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Group, Post, User

User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Masha')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostViewsTests.user)

    def test_post_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/profile.html': (
                reverse('posts:profile',
                        kwargs={'username': self.user.username})),
            'posts/group_list.html': (
                reverse('posts:group_list',
                        kwargs={'slug': self.group.slug})),
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/post_detail.html': (
                reverse('posts:post_detail',
                        kwargs={'post_id': self.post.id})),
            'posts/update_post.html': (
                reverse('posts:post_edit',
                        kwargs={'post_id': self.post.id})),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_group_list_profile_show_correct_context(self):
        """Шаблоны index group_list profile сформированы
        с правильным контекстом."""
        reverse_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        ]
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                author_0 = first_object.author
                text_0 = first_object.text
                group_0 = first_object.group
                self.assertEqual(author_0, self.user)
                self.assertEqual(text_0, 'Тестовый текст')
                self.assertEqual(group_0, self.group)

    def test_post_detail_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        post_0 = response.context.get('post')
        text_0 = post_0.text
        author_0 = post_0.author
        group_0 = post_0.group
        self.assertEqual(author_0, self.user)
        self.assertEqual(text_0, 'Тестовый текст')
        self.assertEqual(group_0, self.group)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for fields_name, expected in form_fields.items():
            with self.subTest(value=fields_name):
                form_field = response.context.get(
                    'form').fields.get(fields_name)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for fields_name, expected in form_fields.items():
            with self.subTest(value=fields_name):
                form_field = response.context.get(
                    'form').fields.get(fields_name)
                self.assertIsInstance(form_field, expected)

    def test_post_appeared_in_index_group_list_profile(self):
        """Пост появляется на страницах сайта."""
        reverse_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        ]
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIn(self.post, response.context['page_obj'])

    def test_post_didnot_appear_on_the_other_groups_page(self):
        """Пост не попал в группу, для которой не был предназначен."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertIsNot(self.post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        for i in range(13):
            Post.objects.create(author=cls.user,
                                group=cls.group,
                                text=f'Пост {i}')

    def setUp(self):
        self.guest_client = Client()

    def test_paginator(self):
        """Проверка количества постов на странице."""
        url_pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for url in url_pages:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(len(response.context['page_obj']), 10)
                response = self.guest_client.get(url + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
