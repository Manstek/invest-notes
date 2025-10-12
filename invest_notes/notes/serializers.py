from djoser.serializers import UserCreatePasswordRetypeSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import Label

User = get_user_model()


class CustomUserCreateSerializer(UserCreatePasswordRetypeSerializer):

    email = serializers.EmailField(
        required=True, allow_blank=False,
        validators=[UniqueValidator(
            queryset=User.objects.all(),
            message="A user with that email already exists.")])

    class Meta:
        model = User
        fields = ('username', 'email', 'password')


class LabelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Label
        fields = ('id', 'title')

    def validate_title(self, value):

        value = ' '.join(value.split())

        if value == '':
            raise serializers.ValidationError(
                'Cannot pass an empty value'
            )

        owner = self.context['request'].user

        if self.instance:
            owner = self.instance.owner

        label_qs = Label.objects.filter(title__iexact=value, owner=owner)

        if self.instance:
            label_qs = label_qs.exclude(pk=self.instance.pk)

        if label_qs.exists():
            raise serializers.ValidationError(
                'You have already created a label with this name.')
        return value
