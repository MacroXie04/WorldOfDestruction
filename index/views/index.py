from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from index.forms.CreateGameForm import CreateGameForm
from index.forms.CountryForm import CountryForm
from index.models import Game, Country

@login_required
def create_game(request):
    """
    创建游戏。用户填写游戏名称，创建游戏之后重定向到创建国家的页面。
    """
    if request.method == 'POST':
        form = CreateGameForm(request.POST)
        if form.is_valid():
            game = form.save()
            # 创建游戏后直接跳转到创建国家页面
            return redirect('create_country', game_id=game.id)
    else:
        form = CreateGameForm()
    return render(request, 'create_game.html', {'form': form})

@login_required
def create_country(request, game_id):
    """
    创建国家。当用户创建游戏后或在加入游戏时，均使用此视图创建国家，并将该国家添加到游戏中。
    """
    game = get_object_or_404(Game, id=game_id)
    if request.method == 'POST':
        form = CountryForm(request.POST)
        if form.is_valid():
            country = form.save(commit=False)
            country.user = request.user
            country.save()
            # 将新创建的国家加入游戏
            game.countries.add(country)
            return redirect('game_detail', game_id=game.id)
    else:
        form = CountryForm()
    return render(request, 'create_country.html', {'form': form, 'game': game})

@login_required
def find_games(request):
    """
    查找可加入的游戏，显示所有允许加入且未结束的游戏。
    """
    games = Game.objects.filter(can_join=True, finished=False)
    return render(request, 'find_games.html', {'games': games})

@login_required
def game_detail(request, game_id):
    """
    显示游戏详情，包括当前玩家及其国家信息，同时提供“开始游戏”按钮。
    """
    game = get_object_or_404(Game, id=game_id)
    countries = game.countries.all()
    return render(request, 'game_detail.html', {'game': game, 'countries': countries})

@login_required
def start_game(request, game_id):
    """
    开始游戏逻辑，此处简单将游戏状态更新为不可再加入（你可在此扩展更多开始游戏的逻辑）。
    """
    game = get_object_or_404(Game, id=game_id)
    if request.method == 'POST':
        game.can_join = False
        game.save()
        return redirect('game_detail', game_id=game.id)
    return redirect('game_detail', game_id=game.id)