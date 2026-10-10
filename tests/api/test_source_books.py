from rest_framework.test import APIClient

from tests.base import CacheClearingTestCase
from tests.factories import make_question, make_user


class SourceBookListTests(CacheClearingTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user()
        self.client = APIClient()
        self.client.force_login(self.user)

    def test_missing_and_blank_titles_do_not_break_book_list(self):
        for title in (None, '', '   ', '\t\n'):
            make_question(owner=self.user, source_document=title)
        for _ in range(2):
            make_question(owner=self.user, source_document='كتاب المصدر')
        make_question(owner=self.user, source_document=' Kaplan ')
        make_question(owner=self.user, source_document='Private book', is_draft=True,
                      draft_owner=self.user)

        response = self.client.get('/api/v1/questions/source-books/')

        self.assertEqual(response.status_code, 200)
        books = {item['name']: item['count'] for item in response.json()['data']['items']}
        self.assertEqual(books, {'كتاب المصدر': 2, ' Kaplan ': 1})

    def test_only_missing_titles_returns_empty_list(self):
        make_question(owner=self.user, source_document=None)
        response = self.client.get('/api/v1/questions/source-books/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['items'], [])
