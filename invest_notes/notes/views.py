from rest_framework import viewsets, mixins, filters
from rest_framework.permissions import IsAuthenticated
from .models import Label
from .serializers import LabelSerializer
from .permissions import IsAuthor
from djoser import views


class UserViewSet(views.UserViewSet):
    http_method_names = ['get', 'post', 'patch']


class LabelViewSet(viewsets.GenericViewSet, mixins.DestroyModelMixin,
                   mixins.CreateModelMixin, mixins.ListModelMixin,
                   mixins.UpdateModelMixin, mixins.RetrieveModelMixin):
    queryset = Label.objects.all()
    serializer_class = LabelSerializer
    http_method_names = ['post', 'get', 'delete', 'patch']
    filter_backends = [filters.SearchFilter]
    search_fields = ['title',]

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), ]
        return [IsAuthor(), ]

    def get_queryset(self):
        return Label.objects.filter(owner__id=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
