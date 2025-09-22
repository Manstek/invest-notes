from djoser.serializers import UserCreatePasswordRetypeSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class CustomUserCreateSerializer(UserCreatePasswordRetypeSerializer):

    email = serializers.EmailField(required=True, allow_blank=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')
