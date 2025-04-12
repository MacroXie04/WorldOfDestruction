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
    path('create_game/', index.create_game, name='create_game'),
    path('create_country/<int:game_id>/', index.create_country, name='create_country'),
    path('find_games/', index.find_games, name='find_games'),
    path('game_detail/<int:game_id>/', index.game_detail, name='game_detail'),
    path('start_game/<int:game_id>/', index.start_game, name='start_game'),


]