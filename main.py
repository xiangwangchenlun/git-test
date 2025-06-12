import random
import itertools

# 定义扑克牌
suits = ['♠', '♥', '♣', '♦']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
deck = [f"{suit}{rank}" for suit in suits for rank in ranks]
rank_value = {rank: i for i, rank in enumerate(ranks)}

def get_card_rank(card):
    """获取牌的点数"""
    return rank_value[card[1:]]

def get_card_suit(card):
    """获取牌的花色"""
    return card[0]

def deal_cards(num_players, num_cards):
    """发牌，每人num_cards张"""
    if num_cards * num_players > len(deck):
        raise ValueError("牌数不足")
    random.shuffle(deck)
    hands = [deck[i * num_cards:(i + 1) * num_cards] for i in range(num_players)]
    return hands

def evaluate_hand(hand):
    """评估3张牌的牌型"""
    ranks = sorted([get_card_rank(card) for card in hand], reverse=True)
    suits = [get_card_suit(card) for card in hand]

    is_flush = len(set(suits)) == 1
    is_straight = (max(ranks) - min(ranks) == 2 and len(set(ranks)) == 3) or (ranks == [12, 1, 0])
    is_three_of_a_kind = len(set(ranks)) == 1
    is_pair = len(set(ranks)) == 2

    if is_three_of_a_kind:
        return (5, ranks, "豹子")
    elif is_flush and is_straight:
        return (4, ranks, "同花顺")
    elif is_flush:
        return (3, ranks, "同花")
    elif is_straight:
        return (2, ranks, "顺子")
    elif is_pair:
        pair_rank = max([r for r in ranks if ranks.count(r) == 2])
        single_rank = [r for r in ranks if ranks.count(r) == 1][0]
        return (1, [pair_rank, single_rank], "对子")
    else:
        return (0, ranks, "单张")

def compare_hands(hand1, hand2):
    """比较两手牌大小（无花色比较）"""
    type1, ranks1, _ = evaluate_hand(hand1)
    type2, ranks2, _ = evaluate_hand(hand2)

    if type1 != type2:
        return 1 if type1 > type2 else -1
    else:
        for r1, r2 in zip(ranks1, ranks2):
            if r1 != r2:
                return 1 if r1 > r2 else -1
        return 0  # 点数相同，返回平局

def select_best_three(hand):
    """从手中选择炸金花规则下最大的3张牌"""
    if len(hand) < 3:
        return hand
    best_combination = None
    best_score = (-1, [])
    for combo in itertools.combinations(hand, 3):
        score = evaluate_hand(combo)
        if score[:2] > best_score[:2]:
            best_score = score
            best_combination = list(combo)
    return best_combination

def ai_decision(player, current_bet, seen, pot, round_num, has_called, after_see=False):
    """AI 决策逻辑，第二轮起可比牌，消耗跟注筹码，第一轮看牌后必须跟注/加注/弃牌"""
    hand_strength = evaluate_hand(select_best_three(player["hand"]))[0]
    if player["chips"] < current_bet * (2 if seen else 1):
        return "fold"

    pot_odds = current_bet / (pot + current_bet) if pot + current_bet > 0 else 1.0

    # 第一轮看牌后，必须选择跟注、加注或弃牌
    if round_num == 1 and seen and after_see:
        if hand_strength >= 3:  # 强牌优先加注
            return "raise"
        elif hand_strength >= 1 and pot_odds < 0.3:  # 中等牌跟注
            return "call"
        else:
            return "fold"

    # 第二轮及以后，考虑比牌（无论是否看牌）
    if round_num >= 2:
        if hand_strength >= 4:  # 豹子或同花顺
            return "compare"
        elif hand_strength >= 3 and random.random() < 0.7:  # 同花，70%概率比牌
            return "compare"
        elif hand_strength >= 2 and random.random() < 0.3:  # 顺子，30%概率比牌
            return "compare"

    # 已看牌：跟注、加注、弃牌
    if seen:
        if hand_strength >= 3:
            return "raise"
        elif hand_strength >= 1 and pot_odds < 0.25:
            return "call"
        else:
            return "fold"

    # 未看牌：看牌、跟注、加注、弃牌
    if hand_strength >= 4:
        return "raise"
    elif hand_strength >= 2 and pot_odds < 0.3:
        return random.choice(["raise", "call"])
    elif random.random() < 0.4 and round_num <= 3:
        return "see"
    elif pot_odds < 0.2:
        return "call"
    else:
        return "fold"

def play_single_game(num_cards, players, action_order):
    """单局游戏，第二轮起可比牌，消耗跟注筹码，第一轮看牌后必须跟注/加注/弃牌"""
    pot = 0
    base_bet = 10
    current_bet = base_bet

    # 重置玩家状态
    for player in players:
        player["hand"] = None
        player["folded"] = False
        player["seen"] = False
        player["has_called"] = False

    # 发牌
    try:
        hands = deal_cards(num_players=4, num_cards=num_cards)
    except ValueError:
        print("牌数过多，无法发牌！游戏结束")
        return False
    for i, player in enumerate(players):
        if player["chips"] < base_bet:
            print(f"{player['name']} 筹码不足，无法继续游戏")
            return False
        player["hand"] = hands[i]
        player["chips"] -= base_bet
        pot += base_bet
        print(f"{player['name']} 下底注: {base_bet}, 剩余筹码: {player['chips']}")

    round_num = 1
    while True:
        print(f"\n=== 第 {round_num} 轮 ===")
        print(f"当前底池: {pot}, 当前跟注金额: {current_bet}")
        print(f"行动顺序: {' -> '.join(players[i]['name'] for i in action_order)}")

        # 重置每轮的跟注状态
        for player in players:
            player["has_called"] = False

        # 按行动顺序处理玩家和 AI
        for player_idx in action_order:
            player = players[player_idx]
            if player["folded"]:
                continue

            active_opponents = [(i, p) for i, p in enumerate(players) if not p["folded"] and i != player_idx]
            if not active_opponents:
                break  # 没有对手，直接结束轮次

            if player_idx == 0:  # 玩家行动
                if player["seen"]:
                    print(f"\n你的牌: {player['hand']}")
                    print(f"最佳3张牌（按炸金花规则）: {select_best_three(player['hand'])}")
                print(f"{player['name']} 的筹码: {player['chips']}")

                # 构建选项
                valid_choices = []
                if not player["seen"]:
                    valid_choices.append("1")  # 看牌
                valid_choices.extend(["2", "3", "4"])  # 跟注、加注、弃牌
                if round_num >= 2:
                    valid_choices.append("5")  # 第二轮起可比牌

                # 显示选项
                options = []
                if "1" in valid_choices:
                    options.append("(1) 看牌")
                if "2" in valid_choices:
                    options.append("(2) 跟注")
                if "3" in valid_choices:
                    options.append("(3) 加注")
                if "4" in valid_choices:
                    options.append("(4) 弃牌")
                if "5" in valid_choices:
                    options.append("(5) 比牌")
                print("选择行动: " + ", ".join(options))

                while True:
                    try:
                        choice = input(f"输入行动编号 ({'/'.join(valid_choices)}): ")
                        if choice not in valid_choices:
                            print(f"无效输入，请输入 {valid_choices}")
                            continue
                        break
                    except:
                        print("输入错误，请重新输入")

                if choice == "1" and not player["seen"]:
                    player["seen"] = True
                    print(f"你看了牌: {player['hand']}")
                    print(f"最佳3张牌（按炸金花规则）: {select_best_three(player['hand'])}")
                    if round_num == 1:
                        # 第一轮看牌后，必须选择跟注、加注或弃牌
                        print("选择动作: (1) 跟注, (2) 加注, (3) 弃牌")
                        while True:
                            try:
                                choice = input("输入动作编号 (1-3): ")
                                if choice not in ["1", "2", "3"]:
                                    print("无效输入，请输入 1-3")
                                    continue
                                break
                            except:
                                print("输入错误，请重新输入")
                        choice = {"1": "2", "2": "3", "3": "4"}[choice]  # 映射到主选项
                    else:
                        continue  # 第二轮及以后，看牌后结束

                if choice == "2":  # 跟注
                    bet = current_bet * (2 if player["seen"] else 1)
                    if player["chips"] >= bet:
                        player["chips"] -= bet
                        pot += bet
                        player["has_called"] = True
                        print(f"{player['name']} 跟注: {bet}, 剩余筹码: {player['chips']}")
                    else:
                        print(f"{player['name']} 筹码不足，自动弃牌")
                        player["folded"] = True
                    continue  # 跟注后结束本轮行动
                elif choice == "3":  # 加注
                    try:
                        min_raise = current_bet * 2 if player["seen"] else current_bet + 10
                        raise_amount = int(input(f"输入加注金额 (至少 {min_raise}): "))
                        if raise_amount < min_raise:
                            print(f"加注金额过低，至少为 {min_raise}")
                            continue
                        bet = raise_amount * (2 if player["seen"] else 1)
                        if player["chips"] >= bet:
                            player["chips"] -= bet
                            pot += bet
                            current_bet = raise_amount
                            player["has_called"] = True  # 加注也算跟注
                            print(f"{player['name']} 加注: {bet}, 剩余筹码: {player['chips']}")
                        else:
                            print(f"{player['name']} 筹码不足，自动弃牌")
                            player["folded"] = True
                        continue  # 加注后结束本轮行动
                    except ValueError:
                        print("无效输入，跳过此轮")
                        continue
                elif choice == "4":  # 弃牌
                    player["folded"] = True
                    print(f"{player['name']} 弃牌")
                    continue
                elif choice == "5" and round_num >= 2:  # 比牌
                    print("选择比牌对手：")
                    for idx, opp in active_opponents:
                        print(f"({idx}) {opp['name']}")
                    while True:
                        try:
                            opp_idx = int(input("输入对手编号: "))
                            if opp_idx not in [i for i, _ in active_opponents]:
                                print("无效对手编号")
                                continue
                            break
                        except ValueError:
                            print("请输入有效编号")
                    opponent = players[opp_idx]
                    bet = current_bet * (2 if player["seen"] else 1)
                    if player["chips"] >= bet:
                        player["chips"] -= bet
                        pot += bet
                        print(f"{player['name']} 因比牌下注: {bet}, 剩余筹码: {player['chips']}")
                    else:
                        print(f"{player['name']} 筹码不足，自动弃牌")
                        player["folded"] = True
                        continue
                    if opponent["chips"] >= bet:
                        opponent["chips"] -= bet
                        pot += bet
                        print(f"{opponent['name']} 因比牌下注: {bet}, 剩余筹码: {opponent['chips']}")
                    else:
                        print(f"{opponent['name']} 筹码不足，自动弃牌")
                        opponent["folded"] = True
                        continue
                    player_hand = select_best_three(player["hand"])
                    opponent_hand = select_best_three(opponent["hand"])
                    result = compare_hands(player_hand, opponent_hand)
                    print(f"\n比牌: {player['name']} 的牌 {player_hand} vs {opponent['name']} 的牌 {opponent_hand}")
                    if result > 0:
                        print(f"{player['name']} 获胜！{opponent['name']} 弃牌")
                        opponent["folded"] = True
                    elif result < 0:
                        print(f"{opponent['name']} 获胜！{player['name']} 弃牌")
                        player["folded"] = True
                    else:
                        print("平局！双方继续")
                    continue  # 比牌后结束本轮行动

            else:  # AI 行动
                ai_action = ai_decision(player, current_bet, player["seen"], pot, round_num, player["has_called"])
                if ai_action == "see":
                    player["seen"] = True
                    print(f"{player['name']} 看牌")
                    if round_num == 1:
                        # 第一轮看牌后，必须选择跟注、加注或弃牌
                        ai_action = ai_decision(player, current_bet, player["seen"], pot, round_num, player["has_called"], after_see=True)
                    else:
                        continue  # 第二轮及以后，看牌后结束轮次

                if ai_action == "call":
                    bet = current_bet * (2 if player["seen"] else 1)
                    if player["chips"] >= bet:
                        player["chips"] -= bet
                        pot += bet
                        player["has_called"] = True
                        print(f"{player['name']} 跟注: {bet}, 剩余筹码: {player['chips']}")
                    else:
                        print(f"{player['name']} 筹码不足，自动弃牌")
                        player["folded"] = True
                    continue
                elif ai_action == "raise":
                    raise_amount = current_bet * 2 if player["seen"] else current_bet + random.randint(10, 20)
                    bet = raise_amount * (2 if player["seen"] else 1)
                    if player["chips"] >= bet:
                        player["chips"] -= bet
                        pot += bet
                        current_bet = raise_amount
                        player["has_called"] = True
                        print(f"{player['name']} 加注: {bet}, 剩余筹码: {player['chips']}")
                    else:
                        print(f"{player['name']} 筹码不足，自动弃牌")
                        player["folded"] = True
                    continue
                elif ai_action == "fold":
                    player["folded"] = True
                    print(f"{player['name']} 弃牌")
                    continue
                elif ai_action == "compare" and round_num >= 2:
                    active_opponents = [p for i, p in enumerate(players) if not p["folded"] and i != player_idx]
                    if active_opponents:
                        opponent = random.choice(active_opponents)
                        bet = current_bet * (2 if player["seen"] else 1)
                        if player["chips"] >= bet:
                            player["chips"] -= bet
                            pot += bet
                            print(f"{player['name']} 因比牌下注: {bet}, 剩余筹码: {player['chips']}")
                        else:
                            print(f"{player['name']} 筹码不足，自动弃牌")
                            player["folded"] = True
                            continue
                        if opponent["chips"] >= bet:
                            opponent["chips"] -= bet
                            pot += bet
                            print(f"{opponent['name']} 因比牌下注: {bet}, 剩余筹码: {opponent['chips']}")
                        else:
                            print(f"{opponent['name']} 筹码不足，自动弃牌")
                            opponent["folded"] = True
                            continue
                        player_hand = select_best_three(player["hand"])
                        opponent_hand = select_best_three(opponent["hand"])
                        result = compare_hands(player_hand, opponent_hand)
                        print(f"\n比牌: {player['name']} 的牌 {player_hand} vs {opponent['name']} 的牌 {opponent_hand}")
                        if result > 0:
                            print(f"{player['name']} 获胜！{opponent['name']} 弃牌")
                            opponent["folded"] = True
                        elif result < 0:
                            print(f"{opponent['name']} 获胜！{player['name']} 弃牌")
                            player["folded"] = True
                        else:
                            print("平局！双方继续")
                        continue  # 比牌后结束本轮行动

        # 检查游戏是否结束
        active_players = [p for p in players if not p["folded"]]
        if len(active_players) <= 1:
            break

        round_num += 1
        if round_num > 5:
            break

    # 显示所有玩家的牌
    print("\n=== 本局所有玩家牌 ===")
    for player in players:
        final_hand = select_best_three(player["hand"]) if player["hand"] else []
        score = evaluate_hand(final_hand) if final_hand else (0, [], "无牌")
        status = "已弃牌" if player["folded"] else "未弃牌"
        print(f"{player['name']} (状态: {status})")
        print(f"  手牌: {player['hand']}")
        print(f"  最佳3张牌: {final_hand}, 牌型: {score[2]}")

    # 游戏结束
    active_players = [p for p in players if not p["folded"]]
    if len(active_players) == 1:
        winner = active_players[0]
        winner["chips"] += pot
        print(f"\n{winner['name']} 获胜，赢得底池: {pot}")
        return True

    # 比牌
    print("\n=== 比牌 ===")
    best_players = []
    best_hand = None
    best_score = (-1, [])
    for player in active_players:
        final_hand = select_best_three(player["hand"])
        score = evaluate_hand(final_hand)
        if not best_hand or compare_hands(final_hand, best_hand) > 0:
            best_players = [player]
            best_hand = final_hand
            best_score = score
        elif compare_hands(final_hand, best_hand) == 0:
            best_players.append(player)

    if len(best_players) == 1:
        best_players[0]["chips"] += pot
        print(f"\n{best_players[0]['name']} 获胜，赢得底池: {pot}")
    else:
        split_pot = pot // len(best_players)
        for player in best_players:
            player["chips"] += split_pot
            print(f"\n{player['name']} 平局，赢得底池部分: {split_pot}")
    return True

def play_game():
    """循环运行炸金花游戏"""
    print("欢迎体验4人炸金花！")
    print("规则说明：")
    print("- 牌型顺序：豹子 > 同花顺 > 同花 > 顺子 > 对子 > 单张")
    print("- 第一轮可选择看牌、跟注、加注或弃牌；看牌后必须选择跟注、加注或弃牌")
    print("- 第二轮及以后，未看牌可选择看牌、跟注、加注、弃牌、比牌；已看牌可选择跟注、加注、弃牌、比牌")
    print("- 看牌后后续轮次无看牌选项")
    print("- 比牌从第二轮开始，消耗跟注筹码（未看牌: current_bet，已看牌: current_bet * 2），比牌后跳到下一玩家")
    print("- 看牌后跟注/加注金额为未看牌的两倍")
    print("- 比牌输者弃牌，平局继续")
    print("- 每局行动顺序固定，下一局轮转（如 1-2-3-4 变为 2-3-4-1）")

    # 获取发牌数量
    while True:
        try:
            num_cards = int(input("请输入每人发牌数量（至少3张，最多13张）："))
            if 3 <= num_cards <= 13:
                break
            print("请输入3到13之间的数字")
        except ValueError:
            print("请输入有效的数字")

    # 初始化玩家
    players = [
        {"name": "You", "chips": 100, "hand": None, "folded": False, "seen": False, "has_called": False},
        {"name": "AI1", "chips": 100, "hand": None, "folded": False, "seen": False, "has_called": False},
        {"name": "AI2", "chips": 100, "hand": None, "folded": False, "seen": False, "has_called": False},
        {"name": "AI3", "chips": 100, "hand": None, "folded": False, "seen": False, "has_called": False}
    ]

    # 初始化行动顺序
    action_order = [0, 1, 2, 3]  # 玩家, AI1, AI2, AI3

    game_count = 0
    while True:
        game_count += 1
        print(f"\n=== 第 {game_count} 局 ===")
        # 运行单局
        if not play_single_game(num_cards, players, action_order):
            break

        # 检查筹码为0
        for player in players:
            if player["chips"] <= 0:
                print(f"\n{player['name']} 筹码为0，游戏结束！")
                print("\n最终筹码：")
                for player in players:
                    print(f"{player['name']}: {player['chips']} 筹码")
                return

        # 显示筹码
        print("\n当前筹码：")
        for player in players:
            print(f"{player['name']}: {player['chips']} 筹码")

        # 检查是否有人有足够筹码
        active_players = [p for p in players if p["chips"] >= 10]
        if len(active_players) < 2:
            print("\n游戏结束：少于2名玩家有足够筹码！")
            print("\n最终筹码：")
            for player in players:
                print(f"{player['name']}: {player['chips']} 筹码")
            break

        # 轮转行动顺序
        action_order = action_order[1:] + action_order[:1]
        print(f"下一局行动顺序: {' -> '.join(players[i]['name'] for i in action_order)}")

        # 询问是否继续
        while True:
            continue_game = input("\n是否继续下一局？(y/n): ").lower()
            if continue_game in ['y', 'n']:
                break
            print("请输入 y 或 n")

        if continue_game == 'n':
            print("\n游戏结束！最终筹码：")
            for player in players:
                print(f"{player['name']}: {player['chips']} 筹码")
            break

# 运行游戏
play_game()