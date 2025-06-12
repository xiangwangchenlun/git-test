import random
import itertools

# 定义扑克牌
suits = ['♠', '♥', '♣', '♦']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
deck = [f"{suit}{rank}" for suit in suits for rank in ranks]

# 牌值映射
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
    """比较两手牌大小"""
    type1, ranks1, _ = evaluate_hand(hand1)
    type2, ranks2, _ = evaluate_hand(hand2)

    if type1 != type2:
        return 1 if type1 > type2 else -1
    else:
        for r1, r2 in zip(ranks1, ranks2):
            if r1 != r2:
                return 1 if r1 > r2 else -1
        suits1 = sorted([get_card_suit(card) for card in hand1], key=lambda x: suits.index(x), reverse=True)
        suits2 = sorted([get_card_suit(card) for card in hand2], key=lambda x: suits.index(x), reverse=True)
        for s1, s2 in zip(suits1, suits2):
            if s1 != s2:
                return 1 if suits.index(s1) > suits.index(s2) else -1
        return 0


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
        elif score[:2] == best_score[:2]:
            current_suits = sorted([get_card_suit(card) for card in combo], key=lambda x: suits.index(x), reverse=True)
            best_suits = sorted([get_card_suit(card) for card in best_combination], key=lambda x: suits.index(x),
                                reverse=True)
            if current_suits > best_suits:
                best_combination = list(combo)
                best_score = score
    return best_combination


def ai_decision(player, current_bet, seen):
    """AI简单决策逻辑"""
    hand_strength = evaluate_hand(select_best_three(player["hand"]))[0]
    if player["chips"] < current_bet * (2 if seen else 1):
        return "fold"
    if not seen:
        if hand_strength >= 3:
            return random.choice(["raise", "call"])
        elif random.random() < 0.3:
            return "see"
        elif random.random() < 0.2:
            return "fold"
        else:
            return "call"
    else:
        if hand_strength >= 4:
            return "raise"
        elif hand_strength >= 2:
            return random.choice(["raise", "call"])
        elif hand_strength == 1 and random.random() < 0.5:
            return "call"
        else:
            return "fold"


def play_single_game(num_cards, players):
    """单局游戏"""
    pot = 0
    base_bet = 10
    current_bet = base_bet

    # 重置玩家状态
    for player in players:
        player["hand"] = None
        player["folded"] = False
        player["seen"] = False

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

        # 玩家行动
        if not players[0]["folded"]:
            if players[0]["seen"]:
                print(f"你的牌: {players[0]['hand']}")
                print(f"最佳3张牌（按炸金花规则）: {select_best_three(players[0]['hand'])}")
            print("你的筹码:", players[0]["chips"])
            print("选择行动: (1) 看牌, (2) 跟注, (3) 加注, (4) 弃牌, (5) 比牌")
            while True:
                try:
                    choice = input("输入行动编号 (1-5): ")
                    if choice not in ["1", "2", "3", "4", "5"]:
                        print("无效输入，请输入 1-5")
                        continue
                    break
                except:
                    print("输入错误，请重新输入")

            if choice == "1" and not players[0]["seen"]:
                players[0]["seen"] = True
                print(f"你看了牌: {players[0]['hand']}")
                print(f"最佳3张牌（按炸金花规则）: {select_best_three(players[0]['hand'])}")
            elif choice == "2":
                bet = current_bet * (2 if players[0]["seen"] else 1)
                if players[0]["chips"] >= bet:
                    players[0]["chips"] -= bet
                    pot += bet
                    print(f"你跟注: {bet}, 剩余筹码: {players[0]['chips']}")
                else:
                    print("筹码不足，自动弃牌")
                    players[0]["folded"] = True
            elif choice == "3":
                try:
                    raise_amount = int(input(f"输入加注金额 (至少 {current_bet + 10}): "))
                    if raise_amount < current_bet + 10:
                        print("加注金额过低")
                        continue
                    bet = raise_amount * (2 if players[0]["seen"] else 1)
                    if players[0]["chips"] >= bet:
                        players[0]["chips"] -= bet
                        pot += bet
                        current_bet = raise_amount
                        print(f"你加注: {bet}, 剩余筹码: {players[0]['chips']}")
                    else:
                        print("筹码不足，自动弃牌")
                        players[0]["folded"] = True
                except ValueError:
                    print("无效输入，跳过此轮")
            elif choice == "4":
                players[0]["folded"] = True
                print("你弃牌")
            elif choice == "5":
                active_opponents = [p for p in players[1:] if not p["folded"]]
                if not active_opponents:
                    print("所有对手已弃牌，无法比牌")
                else:
                    break

        # AI行动
        for i in range(1, 4):
            if not players[i]["folded"]:
                ai_action = ai_decision(players[i], current_bet, players[i]["seen"])
                if ai_action == "see":
                    players[i]["seen"] = True
                    print(f"{players[i]['name']} 看牌")
                elif ai_action == "call":
                    bet = current_bet * (2 if players[i]["seen"] else 1)
                    if players[i]["chips"] >= bet:
                        players[i]["chips"] -= bet
                        pot += bet
                        print(f"{players[i]['name']} 跟注: {bet}, 剩余筹码: {players[i]['chips']}")
                    else:
                        print(f"{players[i]['name']} 筹码不足，自动弃牌")
                        players[i]["folded"] = True
                elif ai_action == "raise":
                    raise_amount = current_bet + random.randint(10, 20)
                    bet = raise_amount * (2 if players[i]["seen"] else 1)
                    if players[i]["chips"] >= bet:
                        players[i]["chips"] -= bet
                        pot += bet
                        current_bet = raise_amount
                        print(f"{players[i]['name']} 加注: {bet}, 剩余筹码: {players[i]['chips']}")
                    else:
                        print(f"{players[i]['name']} 筹码不足，自动弃牌")
                        players[i]["folded"] = True
                elif ai_action == "fold":
                    players[i]["folded"] = True
                    print(f"{players[i]['name']} 弃牌")

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
    best_player = None
    best_hand = None
    best_score = (-1, [])
    for player in active_players:
        final_hand = select_best_three(player["hand"])
        score = evaluate_hand(final_hand)
        if not best_hand or compare_hands(final_hand, best_hand) > 0:
            best_player = player
            best_hand = final_hand
            best_score = score

    best_player["chips"] += pot
    print(f"\n{best_player['name']} 获胜，赢得底池: {pot}")
    return True


def play_game():
    """循环运行炸金花游戏"""
    print("欢迎体验4人炸金花！")

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
        {"name": "You", "chips": 100, "hand": None, "folded": False, "seen": False},
        {"name": "AI1", "chips": 100, "hand": None, "folded": False, "seen": False},
        {"name": "AI2", "chips": 100, "hand": None, "folded": False, "seen": False},
        {"name": "AI3", "chips": 100, "hand": None, "folded": False, "seen": False}
    ]

    game_count = 0
    while True:
        game_count += 1
        print(f"\n=== 第 {game_count} 局 ===")
        # 运行单局
        if not play_single_game(num_cards, players):
            break

        # 检查筹码为0
        for player in players:
            if player["chips"] <= 0:
                print(f"\n{player['name']} 筹码为0，游戏结束！")
                print("\n最终筹码：")
                for p in players:
                    print(f"{p['name']}: {p['chips']} 筹码")
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
            for p in players:
                print(f"{p['name']}: {p['chips']} 筹码")
            break

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