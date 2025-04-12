from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from index.forms.CountryForm import CountryForm
from index.forms.CreateGameForm import CreateGameForm
from index.models import *


@login_required(login_url='/login/')
def create_game(request):
    if request.method == 'POST':
        form = CreateGameForm(request.POST)
        if form.is_valid():
            game = form.save()
            return redirect('create_country', game_id=game.id)
    else:
        form = CreateGameForm()
    return render(request, 'create_game.html', {'form': form})


@login_required(login_url='/login/')
def create_country(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    # check the user if already joined the game
    if game.countries.filter(user=request.user).exists():
        return redirect('game_detail', game_id=game.id)

    if request.method == 'POST':
        form = CountryForm(request.POST)
        if form.is_valid():
            country = form.save(commit=False)
            country.user = request.user
            country.save()
            game.countries.add(country)
            return redirect('game_detail', game_id=game.id)
    else:
        form = CountryForm()
    return render(request, 'create_country.html', {'form': form, 'game': game})


@login_required(login_url='/login/')
def find_games(request):
    games = Game.objects.filter(can_join=True, finished=False)
    for game in games:
        game.user_joined = game.countries.filter(user=request.user).exists()
    return render(request, 'find_games.html', {'games': games})


@login_required(login_url='/login/')
def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    countries = game.countries.all()
    return render(request, 'game_detail.html', {'game': game, 'countries': countries})


@login_required(login_url='/login/')
def start_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if request.method == 'POST':
        game.can_join = False
        game.save()
        return redirect('game_room', game_id=game.id)
    return redirect('game_room', game_id=game.id)


@login_required(login_url='/login/')
def game_room(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    try:
        my_country = game.countries.get(user=request.user)
    except Country.DoesNotExist:
        return redirect('create_country', game_id=game.id)
    countries = list(game.countries.all().order_by('created'))
    active_country = get_active_country(game)
    shop_weapons = Weapon.objects.all()
    shop_tools = Tools.objects.all()
    # TODO: 信息更新
    context = {
        'game': game,
        'my_country': my_country,
        'countries': countries,
        'active_country': active_country,
        'shop_weapons': shop_weapons,
        'shop_tools': shop_tools,
    }
    return render(request, 'game_room.html', context)

