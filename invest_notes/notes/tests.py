from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from djoser.utils import encode_uid
from django.conf import settings
from notes.models import Label


User = get_user_model()

JWT_CREATE = 'jwt-create'
JWT_REFRESH = 'jwt-refresh'

USER_LIST = 'user-list'
USER_ACTIVATION = 'user-activation'
USER_ME = 'user-me'

LABEL_LIST = 'labels-list'
LABEL_DETAIL = 'labels-detail'

AUTH_PREFIX = settings.SIMPLE_JWT['AUTH_HEADER_TYPES'][0]


class TestSignUP(APITestCase):

    @classmethod
    def setUpTestData(cls):

        cls.URL_JWT_CREATE = reverse(JWT_CREATE)
        cls.URL_USER_LIST = reverse(USER_LIST)

        cls.data_signup = {
            "username": "user1",
            "email": "user1@test.com",
            "password": "testpwd123123",
            "re_password": "testpwd123123"
        }

        cls.data_active_user = {
            "username": "user2",
            "email": "user2@test.com",
            "password": "user2",
        }
        cls.active_user = User.objects.create_user(
            username=cls.data_active_user['username'],
            password=cls.data_active_user['password'],
            email=cls.data_active_user['email'],
            is_active=True)

    def test_can_user_signup(self):
        response = self.client.post(self.URL_USER_LIST, self.data_signup,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         'Ошибка регистрации пользователя')
        user = User.objects.get(username=self.data_signup["username"])
        self.assertFalse(user.is_active,
                         'Зарегестрированный пользователь сразу активирован')
        response = self.client.post(self.URL_JWT_CREATE, self.data_signup,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED,
                         'Неактивированный пользователь может получить токен')

    def test_signup_with_exists_email(self):
        data = self.data_active_user.copy()
        data['username'] = 'replace_username'
        response = self.client.post(self.URL_USER_LIST, data, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST,
            'Можно зарегестрироваться с одинаковыми email адресами')

    def test_signup_with_not_valid_email(self):
        data = self.data_active_user.copy()
        data['email'] = 'not_valid_email@ru'
        response = self.client.post(self.URL_USER_LIST, data, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST,
            'Можно зарегестрироваться с некорректным email-адресом')

    def test_signup_without_email(self):
        data = self.data_signup.copy()
        data.pop('email')
        response = self.client.post(self.URL_USER_LIST, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                         'Можно зарегестрироваться без email')


class TestActivation(APITestCase):

    @classmethod
    def setUpTestData(cls):

        cls.URL_JWT_CREATE = reverse(JWT_CREATE)
        cls.URL_USER_LIST = reverse(USER_LIST)
        cls.URL_USER_ACTIVATION = reverse(USER_ACTIVATION)
        cls.URL_USER_ME = reverse(USER_ME)

        cls.AUTH_PREFIX = AUTH_PREFIX

        cls.data_signup = {
            "username": "user1",
            "email": "user1@test.com",
            "password": "testpwd123123",
            "re_password": "testpwd123123"
        }

    def test_can_user_activate_account(self):
        self.client.post(self.URL_USER_LIST, self.data_signup, format='json')
        user = User.objects.get(username=self.data_signup['username'])
        uid = encode_uid(user.pk)
        token = default_token_generator.make_token(user)
        data_for_activate = {
            "uid": uid,
            "token": token
        }
        response = self.client.post(self.URL_USER_ACTIVATION,
                                    data_for_activate, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT,
                         'Пользователь не может активировать свой аккаунт')
        response = self.client.post(self.URL_USER_ACTIVATION,
                                    data_for_activate, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN,
            'Пользователь может несколько раз активировать аккаунт')
        user = User.objects.get(username=self.data_signup['username'])
        self.assertTrue(
            user.is_active, 'Пользователь не активируется по ссылке из письма')
        access_response = self.client.post(self.URL_JWT_CREATE,
                                           data=self.data_signup,
                                           format='json')
        access_token = access_response.data['access']
        response = self.client.get(
            self.URL_USER_ME,
            HTTP_AUTHORIZATION=f"{self.AUTH_PREFIX} {access_token}")
        self.assertEqual(
            response.status_code, status.HTTP_200_OK,
            'Невозможно авторизоваться с валидным access-токеном.')

    def test_can_user_activate_account_with_random_token_uid(self):
        self.client.post(self.URL_USER_LIST, self.data_signup, format='json')
        random_data_for_activate = {
            "uid": "random_uid",
            "token": "random_token"
        }
        response = self.client.post(self.URL_USER_ACTIVATION,
                                    random_data_for_activate, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST,
            'Пользователь может активировать аккаунт с рандомными данными')


class TestJWT(APITestCase):

    @classmethod
    def setUpTestData(cls):

        cls.URL_JWT_CREATE = reverse(JWT_CREATE)
        cls.URL_JWT_REFRESH = reverse(JWT_REFRESH)
        cls.URL_USER_ME = reverse(USER_ME)

        cls.AUTH_PREFIX = AUTH_PREFIX

        cls.data_active_user = {
            "username": "user2",
            "email": "user2@test.com",
            "password": "user2",
        }
        cls.active_user = User.objects.create_user(
            username=cls.data_active_user['username'],
            password=cls.data_active_user['password'],
            email=cls.data_active_user['email'],
            is_active=True)

    def test_can_user_create_jwt(self):
        response = self.client.post(self.URL_JWT_CREATE,
                                    data=self.data_active_user,
                                    format='json')
        self.assertEqual(
            response.status_code, status.HTTP_200_OK,
            'Активированный пользователь не может получить JWT-токен')

    def test_jwt_issue_ok(self):
        response = self.client.post(self.URL_JWT_CREATE,
                                    data=self.data_active_user,
                                    format='json')
        self.assertCountEqual(
            response.data.keys(), ['refresh', 'access'],
            ('При получении токена в ответе содержатся ещё поля, '
             'помимо "access" и "refresh"'))
        self.assertNotEqual(len(response.data['access']), '',
                            'Access-токен содержит в себе пустую строку')
        self.assertNotEqual(len(response.data['refresh']), '',
                            'Refresh-токен содержит в себе пустую строку')
        self.assertGreaterEqual(response.data['access'].count('.'), 2)
        self.assertGreaterEqual(response.data['refresh'].count('.'), 2)

    def test_jwt_allows_access(self):
        access_response = self.client.post(self.URL_JWT_CREATE,
                                           data=self.data_active_user,
                                           format='json')
        access_token = access_response.data['access']
        response = self.client.get(
            self.URL_USER_ME,
            HTTP_AUTHORIZATION=f"{self.AUTH_PREFIX} {access_token}")
        self.assertEqual(
            response.status_code, status.HTTP_200_OK,
            'Невозможно авторизоваться с валидным access-токеном')
        self.assertCountEqual(
            response.data.keys(), ['id', 'username', 'email'],
            f'Эндпоинт {self.URL_USER_ME} содержит лишние поля')
        self.assertEqual(
            response.data['username'], self.data_active_user['username'],
            'Username не совпадает')
        self.assertEqual(
            response.data['email'], self.data_active_user['email'],
            'Email не совпадает')

    def test_jwt_refresh(self):
        access_response = self.client.post(self.URL_JWT_CREATE,
                                           data=self.data_active_user,
                                           format='json')
        refresh_token = access_response.data['refresh']
        uncorrect_refresh = 'rubbish43254353453'
        response = self.client.post(self.URL_JWT_REFRESH,
                                    {'refresh': uncorrect_refresh},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED,
                         'Можно обновить токен с непрвильным refresh-токеном')
        response = self.client.post(self.URL_JWT_REFRESH,
                                    {'refresh': refresh_token},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         'Не работает обновление токена по refresh')
        new_access = response.data['access']
        response = self.client.get(
            self.URL_USER_ME,
            HTTP_AUTHORIZATION=f"{self.AUTH_PREFIX} {new_access}")
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         'Новый access-токен не работает')

    def test_jwt_uncorrect_password(self):
        data = self.data_active_user.copy()
        data['password'] = 'not-correct-pwd'
        response = self.client.post(self.URL_JWT_CREATE,
                                    data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestUsersListMethods(APITestCase):

    @classmethod
    def setUpTestData(cls):

        cls.URL_JWT_CREATE = reverse(JWT_CREATE)
        cls.URL_USER_LIST = reverse(USER_LIST)
        cls.URL_USER_ME = reverse(USER_ME)

        cls.AUTH_PREFIX = AUTH_PREFIX

        cls.data_active_user = {
            "username": "user2",
            "email": "user2@test.com",
            "password": "user2",
        }
        cls.active_user = User.objects.create_user(
            username=cls.data_active_user['username'],
            password=cls.data_active_user['password'],
            email=cls.data_active_user['email'],
            is_active=True)

    def test_unauthorized_delete_user(self):
        response = self.client.delete(self.URL_USER_LIST)
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED,
            'Неавторизованный пользователь может удалять аккаунты')

    def test_unauthorized_put_user(self):
        response = self.client.put(self.URL_USER_LIST, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED,
            'Неавторизованный пользователь может обновлять аккаунты.')

    def test_unauthorized_patch_user(self):
        response = self.client.patch(self.URL_USER_LIST, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED,
            'Неавторизованный пользователь может частично обновлять аккаунты')

    def test_authorized_user_delete_put_patch_user(self):
        access_response = self.client.post(self.URL_JWT_CREATE,
                                           data=self.data_active_user,
                                           format='json')
        access_token = access_response.data['access']
        self.client.credentials(
            HTTP_AUTHORIZATION=f"{self.AUTH_PREFIX} {access_token}")
        response = self.client.delete(self.URL_USER_LIST)
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED,
            'Авторизованный пользователь может удалять аккаунты.')
        response = self.client.put(self.URL_USER_LIST, data={}, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED,
            ('Авторизованный пользователь может '
             'полностью редактировать аккаунты.'))
        response = self.client.patch(self.URL_USER_LIST,
                                     data={}, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED,
            ('Авторизованный пользователь может '
             'частично редактировать аккаунты.'))
        self.assertIn('Allow', response.headers)
        self.assertCountEqual(
            [m.strip() for m in response.headers['Allow'].split(',')],
            ['GET', 'POST'],
            (f'Разрешено больше методов у эндпоинта {USER_LIST},'
             ' чем ожидалось')
        )

    def test_unauthorized_get_userme(self):
        response = self.client.get(self.URL_USER_ME)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestLabelsListDetailMethodsAnonymous(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.data_owner = {
            "username": "owner",
            "email": "owner@test.com",
            "password": "testpwd123123",
            "re_password": "testpwd123123"
        }
        cls.owner = User.objects.create_user(
            username=cls.data_owner['username'],
            password=cls.data_owner['password'],
            email=cls.data_owner['email'],
            is_active=True
        )
        cls.data_label = {
            "title": "label_1"
        }
        cls.label = Label.objects.create(title=cls.data_label["title"],
                                         owner=cls.owner)

        cls.URL_LABEL_LIST = reverse(LABEL_LIST)
        cls.URL_LABEL_DETAIL = reverse(LABEL_DETAIL, args=[cls.label.id])

    def test_unauthorized_not_allow(self):
        response = self.client.get(self.URL_LABEL_LIST)
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED,
            'Неавторизованный пользователь может посмотреть списко меток')
        response = self.client.get(self.URL_LABEL_DETAIL)
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED,
            'Неавторизованный пользователь может посмотреть про метку')
        response = self.client.post(self.URL_LABEL_LIST, self.data_label)
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED,
            'Неавторизованный пользователь может создать метку'
        )
        response = self.client.delete(self.URL_LABEL_DETAIL)
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED,
            'Неавторизованный пользователь может удалять метки'
        )
        response = self.client.patch(self.URL_LABEL_DETAIL,
                                     {'title': 'label_update'})
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED,
            'Неавторизованный пользователь может обновлять метки'
        )
        self.assertEqual(self.label.title, self.data_label['title'],
                         'Неавторизованный пользователь может изменить метку')


class TestCreateLabel(APITestCase):

    @classmethod
    def setUpTestData(cls):

        cls.URL_JWT_CREATE = reverse(JWT_CREATE)
        cls.URL_LABEL_LIST = reverse(LABEL_LIST)

        cls.AUTH_PREFIX = AUTH_PREFIX

        cls.data_user = {
            "username": "user",
            "email": "user@test.com",
            "password": "testpwd123123",
            "re_password": "testpwd123123"
        }
        cls.user = User.objects.create_user(
            username=cls.data_user['username'],
            password=cls.data_user['password'],
            email=cls.data_user['email'],
            is_active=True
        )

        cls.data_label_1 = {
            "title": "label_1"
        }

        cls.data_user_label = {
            "title": "test label"
        }
        cls.user_label_with_spaces = {
            "title": "    test    label  spaces   "
        }
        cls.user_label_with_spaces_uppers = {
            "title": "    TEST    LABEL  SPACES   "
        }
        cls.data_empty_label = {
            "title": " "
        }
        cls.user_label = Label.objects.create(
            owner=cls.user, title=cls.data_user_label["title"])
        cls.count_user_label = 1

    def test_can_user_create_label(self):
        response = self.client.post(self.URL_JWT_CREATE, self.data_user)
        access_token = response.data['access']
        self.client.credentials(
            HTTP_AUTHORIZATION=f"{self.AUTH_PREFIX} {access_token}")
        response = self.client.post(self.URL_LABEL_LIST, self.data_label_1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         'Авторизованный пользователь не может создать метку')
        self.assertCountEqual(
            response.data.keys(), ['id', 'title'],
            'При создании ответ API содержит не только id и title')
        label = Label.objects.get(owner=self.user,
                                  title=self.data_label_1['title'])
        self.assertEqual(response.data['id'], label.id,
                         'Ответ API возвращает неправильный id при создании')
        self.assertEqual(
            response.data['title'], label.title,
            'Ответ API возвращает неправильный title при создании')
        self.assertEqual(
            label.owner, self.user,
            'При создании неправильно подставляется owner у метки')

    def test_can_user_create_label_with_spaces(self):
        response = self.client.post(self.URL_JWT_CREATE, self.data_user)
        access_token = response.data['access']
        self.client.credentials(
            HTTP_AUTHORIZATION=f"{self.AUTH_PREFIX} {access_token}")
        response = self.client.post(self.URL_LABEL_LIST, self.data_empty_label)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                         'Пользователь может создать пустую метку')
        response = self.client.post(
            self.URL_LABEL_LIST, self.user_label_with_spaces)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         'Авторизованный пользователь не может создать метку')
        self.assertEqual(
            response.data['title'],
            ' '.join(self.user_label_with_spaces['title'].split()),
            'При создании большие пробелы не убираются')
        response = self.client.post(
            self.URL_LABEL_LIST, self.user_label_with_spaces_uppers)
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST,
            'Пользователь может создать одинаковые метки в разном регистре')

    def test_can_user_create_equal_label(self):
        response = self.client.post(self.URL_JWT_CREATE, self.data_user)
        access_token = response.data['access']
        self.client.credentials(
            HTTP_AUTHORIZATION=f"{self.AUTH_PREFIX} {access_token}")
        response = self.client.post(self.URL_LABEL_LIST, self.data_user_label)
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST,
            'Авторизованный пользователь может создать две одинаковые метки')
        user_labels = self.user.labels.all()
        self.assertEqual(
            user_labels.count(), self.count_user_label,
            'Пользователь создал метки с одним и тем же названием')

    def test_can_user_patch_label(self):
        response = self.client.post(self.URL_JWT_CREATE, self.data_user)
        access_token = response.data['access']
        self.client.credentials(
            HTTP_AUTHORIZATION=f"{self.AUTH_PREFIX} {access_token}")
        self.client.patch(self.URL_LABEL_LIST, self.user_label_with_spaces)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         'Пользователь не может изменить свою метку')
        self.client.patch(self.URL_LABEL_LIST,
                          self.user_label_with_spaces_uppers)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK,
            'Пользователь не может изменить свою метку на такую же')
