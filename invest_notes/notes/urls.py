from django.urls import path, re_path, include
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .views import LabelViewSet, UserViewSet


schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Invest Notes Discription",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="morozov460336@yandex.ru"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'labels', LabelViewSet, basename='labels')

urlpatterns = [
#     path('users/', UserViewSet.as_view({'post': 'create'})),
#     path('users/me/', UserViewSet.as_view({'get': 'me'})),
#     path('users/activation/', UserViewSet.as_view({'post': 'activation'})),

    re_path('', include('djoser.urls.jwt')),
    path('', include(router.urls)),

    path('swagger<format>/',
         schema_view.without_ui(cache_timeout=0),
         name='schema-json'),
    path('swagger/',
         schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),
    path('redoc/',
         schema_view.with_ui('redoc', cache_timeout=0),
         name='schema-redoc'),
]
