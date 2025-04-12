from django.urls import path
from index.views.game_play_api import *
from index.views.game import *
from index.views.user_verification import user_login, register, logout

urlpatterns = [
    # user authentication
    path('login/', user_login, name='login'),
    path('register/', register, name='register'),
    path('logout/', logout, name='logout'),

    # find games
    path('create_game/', create_game, name='create_game'),
    path('create_country/<int:game_id>/', create_country, name='create_country'),
    path('', find_games, name='find_games'),

    # game management
    path('game_detail/<int:game_id>/', game_detail, name='game_detail'),
    path('start_game/<int:game_id>/', start_game, name='start_game'),
    path('game_room/<int:game_id>/', game_room, name='game_room'),
    path('api/game_status/<int:game_id>/', api_game_status, name='api_game_status'),
    path('api/end_turn/<int:game_id>/', end_turn, name='end_turn'),
    path('api/purchase_item/<int:game_id>/', purchase_item, name='purchase_item'),
    path('api/use_item/<int:game_id>/', use_item, name='use_item'),
    path('api/end_turn/<int:game_id>/', end_turn, name='end_turn'),
    path('api/user_inventory/<int:game_id>/', api_user_inventory, name='api_user_inventory'),
]
