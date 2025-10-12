from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from djoser.utils import encode_uid


User = get_user_model()

JWT_CREATE = 'jwt-create'
JWT_REFRESH = 'jwt-refresh'

USER_LIST = 'user-list'
USER_ACTIVATION = 'user-activation'
USER_ME = 'user-me'


class UserAPITestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.URL_JWT_CREATE = reverse(JWT_CREATE)
        cls.URL_JWT_REFRESH = reverse('jwt-refresh')

        cls.URL_USER_LIST = reverse('user-list')
        cls.URL_USER_ACTIVATION = reverse('user-activation')
        cls.URL_USER_ME = reverse('user-me')

        cls.AUTH_PREFIX = 'JWT'

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

        cls.client = APIClient()

    def test_can_user_signup(self):
        response = self.client.post(self.URL_USER_LIST, self.data_signup)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         'Ошибка регистрации пользователя')
        user = User.objects.get(username=self.data_signup["username"])
        self.assertEqual(user.is_active, False,
                         'Зарегестрированный пользователь сразу активирован.')

    def test_signup_with_exists_email(self):
        data = self.data_active_user
        data['username'] = 'replace_username'
        response = self.client.post(self.URL_USER_LIST, data)
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST,
            'Можно зарегестрироваться с одинаковыми email адресами.')

    def test_signup_with_not_valid_email(self):
        data = self.data_active_user
        data['email'] = 'not_valid_email@ru'
        response = self.client.post(self.URL_USER_LIST, data)
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST,
            'Можно зарегестрироваться с некорректным email-адресом.')

    def test_signup_without_email(self):
        self.data_signup.pop('email')
        response = self.client.post(self.URL_USER_LIST, self.data_signup)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                         'Можно зарегестрироваться без email')

    def test_can_user_activate_account(self):
        self.client.post(self.URL_USER_LIST, self.data_signup)
        user = User.objects.get(username=self.data_signup['username'])
        uid = encode_uid(user.pk)
        token = default_token_generator.make_token(user)
        data_for_activate = {
            "uid": uid,
            "token": token
        }
        response = self.client.post(self.URL_USER_ACTIVATION,
                                    data_for_activate)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT,
                         'Пользователь не может активировать свой аккаунт')
        user = User.objects.get(username=self.data_signup['username'])
        self.assertEqual(user.is_active,  True,
                         'Пользователь не активируется по ссылке из письма')
        access_response = self.client.post(self.URL_JWT_CREATE,
                                           data=self.data_signup)
        access_token = access_response.data['access']
        response = self.client.get(
            self.URL_USER_ME,
            HTTP_AUTHORIZATION=f"{self.AUTH_PREFIX} {access_token}")
        self.assertEqual(
            response.status_code, status.HTTP_200_OK,
            'Невозможно авторизоваться с валидным access-токеном.')

    def test_unauthorized_delete_user(self):
        response = self.client.delete(self.URL_USER_LIST)
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED,
            'Неавторизованный пользователь может удалять аккаунты.')

    def test_unauthorized_put_user(self):
        response = self.client.put(self.URL_USER_LIST)
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED,
            'Неавторизованный пользователь может обновлять аккаунты.')

    def test_unauthorized_patch_user(self):
        response = self.client.patch(self.URL_USER_LIST)
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED,
            'Неавторизованный пользователь может частично обновлять аккаунты.')

    def test_can_user_create_jwt(self):
        response = self.client.post(self.URL_JWT_CREATE,
                                    data=self.data_active_user)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK,
            'Активированный пользователь не может получить JWT-токен.')

    def test_jwt_issue_ok(self):
        response = self.client.post(self.URL_JWT_CREATE,
                                    data=self.data_active_user)
        self.assertCountEqual(
            response.data.keys(), ['refresh', 'access'],
            ('При получении токена в ответе содержатся ещё поля, '
             'помиио "access" и "refresh"'))

    def test_jwt_allows_access(self):
        access_response = self.client.post(self.URL_JWT_CREATE,
                                           data=self.data_active_user)
        access_token = access_response.data['access']
        response = self.client.get(
            self.URL_USER_ME,
            HTTP_AUTHORIZATION=f"{self.AUTH_PREFIX} {access_token}")
        self.assertEqual(
            response.status_code, status.HTTP_200_OK,
            'Невозможно авторизоваться с валидным access-токеном.')
        self.assertCountEqual(
            response.data.keys(), ['id', 'username', 'email'],
            f'Эндпоинт {self.URL_USER_ME} содержит лишние поля.')

    def test_jwt_refresh(self):
        access_response = self.client.post(self.URL_JWT_CREATE,
                                           data=self.data_active_user)
        refresh_token = access_response.data['refresh']
        uncorrect_refresh = 'rubbish43254353453'
        response = self.client.post(self.URL_JWT_REFRESH,
                                    {'refresh': uncorrect_refresh})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED,
                         'Можно обновить токен с непрвильным refresh-токеном')
        response = self.client.post(self.URL_JWT_REFRESH,
                                    {'refresh': refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         'Не работает обновление токена по refresh')

    def test_jwt_uncorrect_password(self):
        data = self.data_active_user
        data['password'] = 'not-correct-pwd'
        response = self.client.post(self.URL_JWT_CREATE, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_get_userme(self):
        response = self.client.get(self.URL_USER_ME)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
