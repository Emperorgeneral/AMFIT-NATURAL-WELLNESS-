from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import AmfitAuthenticationForm
from .views import signup_view

app_name = 'users'

urlpatterns = [
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='registration/login.html',
            authentication_form=AmfitAuthenticationForm,
        ),
        name='login',
    ),
    path('signup/', signup_view, name='signup'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]