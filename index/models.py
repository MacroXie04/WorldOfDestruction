from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    # foreign key to user
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # round played
    rounds_played = models.IntegerField(default=0)
    rounds_won = models.IntegerField(default=0)

class Game(models.Model):
    countries = models.ManyToManyField('Country', related_name='games')
    current_round = models.IntegerField(default=1)
    max_actions_per_turn = models.IntegerField(default=2)
    created = models.DateTimeField(auto_now_add=True)
    # Game ends when any country's land reaches 0
    finished = models.BooleanField(default=False)
    can_join = models.BooleanField(default=True)
    name = models.CharField(max_length=100, default="World of Destruction")

    def __str__(self):
        return f"Game #{self.id} - Round {self.current_round}"

class Country(models.Model):
    # foreign key to user
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # country information
    name = models.CharField(max_length=100)

    money = models.IntegerField()
    population = models.IntegerField()
    population_growth_rate = models.FloatField(default=10.0)

    land = models.IntegerField()

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.user}"

class Weapon(models.Model):
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    population_damage = models.IntegerField()
    land_damage = models.IntegerField()

    def __str__(self):
        return f"{self.name} - Price: {self.price} - Population Damage: {self.population_damage} - Land Damage: {self.land_damage}"

class Tools(models.Model):
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    population_increase = models.IntegerField()
    land_increase = models.IntegerField()
    population_growth_rate = models.FloatField(default=10.0)

    def __str__(self):
        return f"{self.name} - Price: {self.price} - Population Damage: {self.population_increase} - Land Damage: {self.land_increase}"

class Turn(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='turns')
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='turns')
    round_number = models.IntegerField()
    used_tools = models.ManyToManyField(Tools, blank=True)
    used_weapons = models.ManyToManyField(Weapon, blank=True)

    class Meta:
        unique_together = ('game', 'country', 'round_number')

    def __str__(self):
        return f"Turn - Game {self.game.id} - {self.country.name} - Round {self.round_number}"
