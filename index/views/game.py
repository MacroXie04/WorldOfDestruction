from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from index.forms.CountryForm import CountryForm
from index.forms.CreateGameForm import CreateGameForm
from index.models import *


@login_required
def create_game(request):
    """
    创建游戏，创建后跳转到创建国家页面。
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
    创建国家：当用户在游戏中创建国家时，先检查当前用户是否已在该游戏中有国家，
    如果已存在则阻止再次创建并直接重定向到游戏详情页面。
    """
    game = get_object_or_404(Game, id=game_id)

    # 检查当前用户是否已在该游戏内拥有国家
    if game.countries.filter(user=request.user).exists():
        # 可选：可以通过 Django messages 提示已加入此游戏
        return redirect('game_detail', game_id=game.id)

    if request.method == 'POST':
        form = CountryForm(request.POST)
        if form.is_valid():
            country = form.save(commit=False)
            country.user = request.user
            country.save()
            # 将新创建的国家加入到游戏中
            game.countries.add(country)
            return redirect('game_detail', game_id=game.id)
    else:
        form = CountryForm()
    return render(request, 'create_country.html', {'form': form, 'game': game})


@login_required
def find_games(request):
    """
    查找允许加入且未结束的游戏，同时标记当前用户是否已加入某个游戏，
    防止重复创建国家。
    """
    games = Game.objects.filter(can_join=True, finished=False)
    for game in games:
        game.user_joined = game.countries.filter(user=request.user).exists()
    return render(request, 'find_games.html', {'games': games})


@login_required
def game_detail(request, game_id):
    """
    显示游戏详情，包括所有玩家和其创建的国家，同时提供“开始游戏”的按钮。
    """
    game = get_object_or_404(Game, id=game_id)
    countries = game.countries.all()
    return render(request, 'game_detail.html', {'game': game, 'countries': countries})


@login_required
def start_game(request, game_id):
    """
    点击游戏开始按键后，把游戏的 can_join 设为 False，
    并重定向到游戏房间页面。
    """
    game = get_object_or_404(Game, id=game_id)
    if request.method == 'POST':
        game.can_join = False
        game.save()
        return redirect('game_room', game_id=game.id)
    return redirect('game_room', game_id=game.id)


@login_required
def game_room(request, game_id):
    """
    游戏房间页面：
    - 显示游戏名称和当前回合
    - 显示其他国家（与自己国家）详细参数
    - 显示本轮轮到哪位国家行动
    - 显示商店（武器和道具）
    - “本轮结束”按钮
    """
    game = get_object_or_404(Game, id=game_id)
    # 确保用户已经加入游戏（已创建国家）
    try:
        my_country = game.countries.get(user=request.user)
    except Country.DoesNotExist:
        return redirect('create_country', game_id=game.id)

    # 获取加入游戏的国家（按创建时间排序，作为回合顺序）
    countries = list(game.countries.all().order_by('created'))
    # 通过Turn记录判断当前回合哪些国家已出手，取第一个没有出手的国家为当前活跃玩家
    active_country = None
    for country in countries:
        if not Turn.objects.filter(game=game, country=country, round_number=game.current_round).exists():
            active_country = country
            break
    # 若所有国家本轮已出手，则本轮结束，应自动更新回合（此处直接令下一轮第一个国家开始）
    if active_country is None and countries:
        game.current_round += 1
        game.save()
        active_country = countries[0]

    # 商店数据：所有 Weapon 和 Tools
    shop_weapons = Weapon.objects.all()
    shop_tools = Tools.objects.all()

    context = {
        'game': game,
        'my_country': my_country,
        'countries': countries,
        'active_country': active_country,
        'shop_weapons': shop_weapons,
        'shop_tools': shop_tools,
        'purchase_limit': game.max_actions_per_turn,  # 每轮可购买道具数量（如2）
    }
    return render(request, 'game_room.html', context)


@login_required
def api_game_status(request, game_id):
    """
    API 接口，供前端 JS 定时获取游戏状态信息，包括：
     - 游戏名称、当前回合
     - 当前轮到的国家信息
     - 所有国家的详细参数（区分是否本人）
     - 商店中所有 Weapon 和 Tools
     - 当前用户本轮剩余购买次数（根据 Turn 记录已购买数计算）
    """
    game = get_object_or_404(Game, id=game_id)
    try:
        my_country = game.countries.get(user=request.user)
    except Country.DoesNotExist:
        return JsonResponse({'error': 'User has not joined this game.'}, status=400)

    countries = list(game.countries.all().order_by('created'))
    active_country = None
    for country in countries:
        if not Turn.objects.filter(game=game, country=country, round_number=game.current_round).exists():
            active_country = country
            break
    if active_country is None and countries:
        active_country = countries[0]

    game_data = {
        'game_name': game.name,
        'current_round': game.current_round,
        'active_country': {'id': active_country.id, 'name': active_country.name} if active_country else None,
        'countries': [
            {
                'id': country.id,
                'name': country.name,
                'money': country.money,
                'population': country.population,
                'population_growth_rate': country.population_growth_rate,
                'land': country.land,
                'is_mine': (country.user == request.user),
            } for country in countries
        ],
        'shop_weapons': [
            {
                'id': w.id,
                'name': w.name,
                'price': w.price,
                'population_damage': w.population_damage,
                'land_damage': w.land_damage,
            } for w in Weapon.objects.all()
        ],
        'shop_tools': [
            {
                'id': t.id,
                'name': t.name,
                'price': t.price,
                'population_increase': t.population_increase,
                'land_increase': t.land_increase,
            } for t in Tools.objects.all()
        ],
        'purchase_limit': game.max_actions_per_turn,
    }
    # 计算当前回合当前用户已购买道具数量
    try:
        turn = Turn.objects.get(game=game, country=my_country, round_number=game.current_round)
        used_count = turn.used_tools.count() + turn.used_weapons.count()
        game_data['purchase_remaining'] = game.max_actions_per_turn - used_count
    except Turn.DoesNotExist:
        game_data['purchase_remaining'] = game.max_actions_per_turn

    return JsonResponse(game_data)


@login_required
def end_turn(request, game_id):
    """
    “本轮结束”接口：
      - 记录当前用户的 Turn（如尚未创建则创建一条空的 Turn 记录，
        代表本轮行动已结束）
      - 返回成功信息，前端可通过再次轮询 api_game_status 获取最新状态
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required.'}, status=400)
    game = get_object_or_404(Game, id=game_id)
    try:
        my_country = game.countries.get(user=request.user)
    except Country.DoesNotExist:
        return JsonResponse({'error': 'User has not joined this game.'}, status=400)
    turn, created = Turn.objects.get_or_create(game=game, country=my_country, round_number=game.current_round)
    return JsonResponse({'message': 'Turn ended.'})


@login_required
def purchase_item(request, game_id):
    """
    购买 Weapon 或 Tool 的接口：
      - 参数 item_type ('weapon' 或 'tool')
      - 参数 item_id
      - 对于武器，需要传递 target_country（目标国家 ID），道具只能作用于自己
      - 检查当前购买数是否已达上限，若未达上限，则将购买项添加到当前 Turn 记录中
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required.'}, status=400)
    game = get_object_or_404(Game, id=game_id)
    try:
        my_country = game.countries.get(user=request.user)
    except Country.DoesNotExist:
        return JsonResponse({'error': 'User has not joined the game.'}, status=400)
    item_type = request.POST.get('item_type')
    item_id = request.POST.get('item_id')
    if not item_type or not item_id:
        return JsonResponse({'error': 'Missing parameters.'}, status=400)
    turn, created = Turn.objects.get_or_create(game=game, country=my_country, round_number=game.current_round)
    used_count = turn.used_tools.count() + turn.used_weapons.count()
    if used_count >= game.max_actions_per_turn:
        return JsonResponse({'error': 'Purchase limit reached for this turn.'}, status=400)
    if item_type == 'weapon':
        try:
            weapon = Weapon.objects.get(pk=item_id)
        except Weapon.DoesNotExist:
            return JsonResponse({'error': 'Weapon not found.'}, status=404)
        target_country_id = request.POST.get('target_country')
        if not target_country_id:
            return JsonResponse({'error': 'Target country required for weapon.'}, status=400)
        try:
            target_country = Country.objects.get(pk=target_country_id)
        except Country.DoesNotExist:
            return JsonResponse({'error': 'Target country not found.'}, status=404)
        # 这里可加入扣除金钱、伤害计算等逻辑
        turn.used_weapons.add(weapon)
        return JsonResponse({'message': f'Weapon {weapon.name} purchased and used on {target_country.name}.'})
    elif item_type == 'tool':
        try:
            tool = Tools.objects.get(pk=item_id)
        except Tools.DoesNotExist:
            return JsonResponse({'error': 'Tool not found.'}, status=404)
        # 工具只能作用于自己
        turn.used_tools.add(tool)
        return JsonResponse({'message': f'Tool {tool.name} purchased and used on your country.'})
    else:
        return JsonResponse({'error': 'Invalid item type.'}, status=400)
