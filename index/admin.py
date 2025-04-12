from django.contrib import admin
from .models import Tools, Weapon, Game, Country, UserProfile, Turn

admin.site.register(Tools)
admin.site.register(Weapon)
admin.site.register(Game)
admin.site.register(Country)
admin.site.register(UserProfile)
admin.site.register(Turn)


