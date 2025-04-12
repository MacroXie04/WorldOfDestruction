from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from index.models import *


@login_required(login_url='/login/')
def api_game_status(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    try:
        my_country = game.countries.get(user=request.user)
    except Country.DoesNotExist:
        return JsonResponse({'error': 'User has not joined this game.'}, status=400)

    countries = list(game.countries.all().order_by('created'))
    active_country = get_active_country(game)

    if game.finished:
        game_status = 'finished'
    else:
        game_status = 'active'

    game_data = {
        'game_status': game_status,
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
    }

    try:
        turn = Turn.objects.get(game=game, country=my_country, round_number=game.current_round)
        used_count = turn.used_tools.count() + turn.used_weapons.count()
        game_data['purchase_remaining'] = game.max_actions_per_turn - used_count
    except Turn.DoesNotExist:
        game_data['purchase_remaining'] = game.max_actions_per_turn

    # get action logs from the database
    try:
        last_actions_qs = ActionLog.objects.filter(game=game).order_by('-timestamp')[:3]
        last_actions = []
        for log in last_actions_qs:
            last_actions.append({
                'timestamp': log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                'action': log.action,
            })
    except Exception:
        last_actions = []

    game_data['last_actions'] = last_actions

    return JsonResponse(game_data)


@login_required(login_url='/login/')
def purchase_item(request, game_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required.'}, status=400)

    game = get_object_or_404(Game, id=game_id)
    # check game status
    if game.finished:
        return JsonResponse({'error': 'Game is not active.'}, status=400)

    # current user country
    try:
        my_country = game.countries.get(user=request.user)
    except Country.DoesNotExist:
        return JsonResponse({'error': 'User has not joined the game.'}, status=400)

    # confirm user can be active
    active_country = get_active_country(game)
    if active_country is None or my_country.id != active_country.id:
        return JsonResponse({'error': 'Please wait for other players'}, status=403)

    # retrieve item type and id from request
    item_type = request.POST.get('item_type')
    item_id = request.POST.get('item_id')

    if not item_type or not item_id:
        return JsonResponse({'error': 'Missing parameters.'}, status=400)

    # get or create current turn
    turn, _ = Turn.objects.get_or_create(
        game=game,
        country=my_country,
        round_number=game.current_round
    )

    # check the purchase limit
    used_count = turn.used_tools.count() + turn.used_weapons.count()
    if used_count >= game.max_actions_per_turn:
        return JsonResponse({'error': 'Purchase limit reached'}, status=400)

    # process weapon purchase
    if item_type == 'weapon':
        try:
            weapon = Weapon.objects.get(pk=item_id)
        except Weapon.DoesNotExist:
            return JsonResponse({'error': 'Weapon not found.'}, status=404)

        # check the user's money
        if my_country.money < weapon.price:
            return JsonResponse({'error': 'Not enough money.'}, status=403)

        # deduct the money
        my_country.money -= weapon.price
        my_country.save()

        # add the weapon to the turn and country inventory
        turn.used_weapons.add(weapon)
        my_country.weapons_inventory.add(weapon)
        return JsonResponse({'message': f'Weapon {weapon.name} is purchased successfully.'})

    # process tool purchase
    elif item_type == 'tool':
        try:
            tool = Tools.objects.get(pk=item_id)
        except Tools.DoesNotExist:
            return JsonResponse({'error': 'Tool not found.'}, status=404)

        # check the user's money
        if my_country.money < tool.price:
            return JsonResponse({'error': 'Not enough money.'}, status=403)

        # deduct the money
        my_country.money -= tool.price
        my_country.save()

        turn.used_tools.add(tool)
        my_country.tools_inventory.add(tool)
        return JsonResponse({'message': f'Tool {tool.name} is purchased successfully.'})

    else:
        return JsonResponse({'error': 'Invalid item type.'}, status=400)


@login_required(login_url='/login/')
def use_item(request, game_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required.'}, status=400)

    game = get_object_or_404(Game, id=game_id)

    try:
        my_country = game.countries.get(user=request.user)
    except Country.DoesNotExist:
        return JsonResponse({'error': 'User has not joined the game.'}, status=400)

    active_country = get_active_country(game)
    if active_country is None or my_country.id != active_country.id:
        return JsonResponse({'error': 'Is not your turn.'}, status=403)

    item_type = request.POST.get('item_type')
    item_id = request.POST.get('item_id')
    if not item_type or not item_id:
        return JsonResponse({'error': 'Missing parameters.'}, status=400)

    # get or create current turn
    turn, created = Turn.objects.get_or_create(game=game, country=my_country, round_number=game.current_round)

    if item_type == 'weapon':
        try:
            weapon = Weapon.objects.get(pk=item_id)
        except Weapon.DoesNotExist:
            return JsonResponse({'error': 'Weapon not found.'}, status=404)
        if not my_country.weapons_inventory.filter(pk=item_id).exists():
            return JsonResponse({'error': 'You do not own this weapon.'}, status=403)

        target_country_id = request.POST.get('target_country')
        if not target_country_id:
            return JsonResponse({'error': 'Target country is required for weapon usage.'}, status=400)
        try:
            target_country = Country.objects.get(pk=target_country_id)
        except Country.DoesNotExist:
            return JsonResponse({'error': 'Target country not found.'}, status=404)

        # 应用武器伤害，减少目标国家的人口和土地（不小于0）
        # TODO: 检查目标国家是否在同一游戏中
        # TODO: 检查目标国家是否已被消灭（人口或土地为0）消灭则游戏结束
        target_country.population = max(0, target_country.population - weapon.population_damage)
        target_country.land = max(0, target_country.land - weapon.land_damage)
        target_country.save()

        # 记录武器使用到 Turn，并从库存中移除该武器（视为消耗品）
        turn.used_weapons.add(weapon)
        my_country.weapons_inventory.remove(weapon)

        # 创建 ActionLog 记录武器使用情况
        ActionLog.objects.create(
            game=game,
            country=my_country,
            action=f"使用武器 {weapon.name} 对 {target_country.name} 造成伤害。"
        )

        return JsonResponse({'message': f'Weapon {weapon.name} used on {target_country.name}.'})

    elif item_type == 'tool':
        try:
            tool = Tools.objects.get(pk=item_id)
        except Tools.DoesNotExist:
            return JsonResponse({'error': 'Tool not found.'}, status=404)
        if not my_country.tools_inventory.filter(pk=item_id).exists():
            return JsonResponse({'error': 'You do not own this tool.'}, status=403)

        # 使用道具对自己国家进行补充（增加人口和土地）
        my_country.population += tool.population_increase
        my_country.land += tool.land_increase
        my_country.save()

        # 记录工具使用到 Turn，并从库存中移除该工具
        turn.used_tools.add(tool)
        my_country.tools_inventory.remove(tool)

        # 创建 ActionLog 记录工具使用情况
        ActionLog.objects.create(
            game=game,
            country=my_country,
            action=f"{my_country.name} 使用道具 {tool.name} 强化国家（增加人口 {tool.population_increase}，增加土地 {tool.land_increase}）。"
        )

        return JsonResponse({'message': f'Tool {tool.name} used. Your country has been reinforced.'})

    else:
        return JsonResponse({'error': 'Invalid item type.'}, status=400)


@login_required(login_url='/login/')
def end_turn(request, game_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required.'}, status=400)

    game = get_object_or_404(Game, id=game_id)

    try:
        my_country = game.countries.get(user=request.user)
    except Country.DoesNotExist:
        return JsonResponse({'error': 'User has not joined the game.'}, status=400)

    # 检查当前是否轮到该玩家操作
    active_country = get_active_country(game)
    if active_country is None or my_country.id != active_country.id:
        return JsonResponse({'error': '现在不是您的回合，无法结束回合。'}, status=403)

    # 获取或创建当前轮的 Turn 记录，并标记其为结束
    turn, created = Turn.objects.get_or_create(game=game, country=my_country, round_number=game.current_round)
    turn.ended = True
    turn.save()

    # 检查当前回合是否所有玩家均结束操作
    countries = list(game.countries.all().order_by('created'))
    all_ended = True
    for country in countries:
        t = Turn.objects.filter(game=game, country=country, round_number=game.current_round).first()
        if not t or not t.ended:
            all_ended = False
            break

    if all_ended:
        game.current_round += 1
        game.save()

    new_active = get_active_country(game)
    return JsonResponse({
        'message': 'Turn ended.',
        'active_country': {'id': new_active.id, 'name': new_active.name} if new_active else None,
        'current_round': game.current_round
    })
