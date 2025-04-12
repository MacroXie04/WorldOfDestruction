from django.contrib.auth.models import User
from django.db import models


# 使用时在函数内部再导入 Turn，避免循环引用
def get_active_country(game):
    from .models import Turn  # 延迟导入确保 Turn 已定义
    countries = list(game.countries.all().order_by('created'))
    for country in countries:
        # 获取当前轮该国家的 Turn 记录（如果存在）
        turn = Turn.objects.filter(game=game, country=country, round_number=game.current_round).first()
        # 如果没有记录，或记录存在但未结束，则返回该国家
        if not turn or not turn.ended:
            return country
    return countries[0] if countries else None


class UserProfile(models.Model):
    # foreign key to user
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # round played
    rounds_played = models.IntegerField(default=0)
    rounds_won = models.IntegerField(default=0)

    def __str__(self):
        return f"Profile of {self.user.username}"


class Weapon(models.Model):
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    population_damage = models.IntegerField()
    land_damage = models.IntegerField()

    def __str__(self):
        return (f"{self.name} - Price: {self.price} - Population Damage: "
                f"{self.population_damage} - Land Damage: {self.land_damage}")


class Tools(models.Model):
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    population_increase = models.IntegerField()
    land_increase = models.IntegerField()
    population_growth_rate = models.FloatField(default=10.0)

    def __str__(self):
        return (f"{self.name} - Price: {self.price} - Population Increase: "
                f"{self.population_increase} - Land Increase: {self.land_increase}")


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
    # 使用 through 模型记录库存
    weapons_inventory = models.ManyToManyField(Weapon, blank=True, through='WeaponInventory', related_name='owned_by')
    tools_inventory = models.ManyToManyField(Tools, blank=True, through='ToolInventory', related_name='owned_by')

    def __str__(self):
        return f"{self.name} - {self.user}"


class WeaponInventory(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    weapon = models.ForeignKey(Weapon, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = ("country", "weapon")

    def __str__(self):
        return f"{self.country} - {self.weapon} x {self.quantity}"


class ToolInventory(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    tool = models.ForeignKey(Tools, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = ("country", "tool")

    def __str__(self):
        return f"{self.country} - {self.tool} x {self.quantity}"


class Game(models.Model):
    countries = models.ManyToManyField(Country, related_name='games')
    current_round = models.IntegerField(default=1)
    max_actions_per_turn = models.IntegerField(default=2)
    created = models.DateTimeField(auto_now_add=True)
    # Game ends when any country's land reaches 0
    finished = models.BooleanField(default=False)
    can_join = models.BooleanField(default=True)
    name = models.CharField(max_length=100, default="World of Destruction")

    def __str__(self):
        return f"Game #{self.id} - Round {self.current_round}"


class Turn(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='turns')
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='turns')
    round_number = models.IntegerField()
    used_tools = models.ManyToManyField(Tools, blank=True)
    used_weapons = models.ManyToManyField(Weapon, blank=True)
    ended = models.BooleanField(default=False)

    class Meta:
        unique_together = ('game', 'country', 'round_number')

    def __str__(self):
        return f"Turn - Game {self.game.id} - {self.country.name} - Round {self.round_number}"


class ActionLog(models.Model):
    game = models.ForeignKey('Game', on_delete=models.CASCADE, related_name='action_logs')
    country = models.ForeignKey('Country', on_delete=models.CASCADE, related_name='action_logs')
    action = models.CharField(max_length=255, help_text="Action performed by the country")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.country.name}: {self.action}"
