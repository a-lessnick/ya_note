# notes/tests/test_routes.py

from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):


    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author,
            slug='note-slug'
        )

        cls.urls_with_slug = (
            ('notes:detail', (cls.note.slug,)),
            ('notes:edit', (cls.note.slug,)),
            ('notes:delete', (cls.note.slug,))
        )
        cls.urls_for_users = (
            ('notes:list', None),
            ('notes:add', None),
            ('notes:success', None),
            *cls.urls_with_slug
        )

        cls.urls_for_anon = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )

    def test_pages_availability(self):
        """Тест доступности страниц анонимному посетителю."""
        for name, args in self.urls_for_anon:
            with self.subTest('Страница недоступна', name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_author(self):
        """Тест доступности страниц для автора заметок."""
        for name, args in self.urls_for_users:
            with self.subTest('Страница не доступна', name=name):
                self.client.force_login(self.author)
                response = self.client.get(reverse(name, args=args))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_reader(self):
        """Тест доступности страниц для читателя заметок."""
        for name, args in self.urls_with_slug:
            with self.subTest("Страница не доступна", name=name):
                self.client.force_login(self.reader)
                response = self.client.get(reverse(name, args=args))
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_redirect_for_anonymous(self):
        """Тест редиректа со страниц для анонимных пользователей."""
        login_url = reverse('users:login')
        for name, args in self.urls_for_users:
            with self.subTest("Страница не доступна", name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
