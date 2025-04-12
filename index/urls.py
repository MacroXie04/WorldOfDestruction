from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from index.views.user_verification import user_login, register, logout
from index.views import index

urlpatterns = [
    # user authentication
    path('login/', user_login, name='login'),
    path('register/', register, name='register'),
    path('logout/', logout, name='logout'),

    # find games
    path('find_games/', index.find_games, name='find_games'),


]