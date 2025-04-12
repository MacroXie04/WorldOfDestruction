from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from index.views.user_verification import user_login, register, logout

urlpatterns = [
    # user authentication
    path('login/', user_login, name='login'),
    path('register/', register, name='register'),
    path('logout/', logout, name='logout'),

    # index page
    path("", index.index, name="index"),

]