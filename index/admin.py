from django.contrib import admin
from .models import *

# manage the tools and weapons
admin.site.register(Tools)
admin.site.register(Weapon)

admin.site.register(CountryTemplate)

admin.site.register(Game)


