import random
from collections import Counter

class Card:
    #Represents a single UNO card with color and value.
    def __init__(self, color, value):
        self.color = color
        self.value = value
        self.is_skip = (value == 'Skip')

    def __repr__(self):
        return f"[{self.color} {self.value}]"

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.color == other.color and self.value == other.value

    def __hash__(self):
        return hash((self.color, self.value))


def create_deck():
    #Creates simplified UNO deck: 4 colors x (0-9 + Skip) = 44 cards.
    colors = ['Red', 'Blue', 'Green', 'Yellow']
    deck = []
    for color in colors:
        for num in range(10):
            deck.append(Card(color, str(num)))
        deck.append(Card(color, 'Skip'))
    random.shuffle(deck)
    return deck

def create_deck():
    #Creates simplified UNO deck: 4 colors x (0-9 + Skip) = 44 cards.
    colors = ['Red', 'Blue', 'Green', 'Yellow']
    deck = []
    for color in colors:
        for num in range(10):
            deck.append(Card(color, str(num)))
        deck.append(Card(color, 'Skip'))
    random.shuffle(deck)
    return deck


class GameState:
    #Complete game state.
    def __init__(self, hands, top_card, deck, current_player=0):
        self.hands = hands
        self.top_card = top_card
        self.deck = deck
        self.current_player = current_player

    def clone(self):
        new_hands = {p: list(cards) for p, cards in self.hands.items()}
        return GameState(new_hands, self.top_card, list(self.deck), self.current_player)


def get_legal_moves(state, player):
    #Returns playable cards or ['draw'] if none valid.
    legal = []
    top = state.top_card
    for card in state.hands[player]:
        if card.color == top.color or card.value == top.value or (card.is_skip and top.is_skip):
            legal.append(card)
    return legal if legal else ['draw']


def apply_move(state, player, move):
    #Applies move and returns new GameState."""
    ns = state.clone()
    if move == 'draw':
        if ns.deck:
            ns.hands[player].append(ns.deck.pop())
        ns.current_player = (player + 1) % 3
    else:
        ns.hands[player].remove(move)
        ns.top_card = move
        ns.current_player = (player + 2) % 3 if move.is_skip else (player + 1) % 3
    return ns


def initialize_game():
    #Creates new game: shuffled deck, 5 cards each, non-Skip top card."""
    deck = create_deck()
    hands = {0: [], 1: [], 2: []}
    for _ in range(5):
        for p in range(3):
            hands[p].append(deck.pop())
    top_card = deck.pop()
    while top_card.is_skip:
        deck.insert(0, top_card)
        top_card = deck.pop()
    return GameState(hands, top_card, deck)

def evaluate_defensive(state, player):
    """Defensive: Score = 50 - 6*C_AI + 3*C_opp + 5*S"""
    c_ai = len(state.hands[player])
    if c_ai == 0: return 1000
    opponents = [p for p in range(3) if p != player]
    for opp in opponents:
        if len(state.hands[opp]) == 0: return -1000
    c_opp = sum(len(state.hands[p]) for p in opponents) / 2.0
    s = sum(1 for c in state.hands[player] if c.is_skip)
    return 50 - 6 * c_ai + 3 * c_opp + 5 * s

def evaluate_offensive(state, player):
    c_ai = len(state.hands[player])
    if c_ai == 0: return 1000
    opponents = [p for p in range(3) if p != player]
    for opp in opponents:
        if len(state.hands[opp]) == 0: return -1000
    c_opp = sum(len(state.hands[p]) for p in opponents) / 2.0
    s = sum(1 for c in state.hands[player] if c.is_skip)
    return 50 - 8 * c_ai + 1 * c_opp + 2 * s


def minimax(state, depth, ai_player):
    #Minimax: MAX for ai_player, MIN for opponents.
    current = state.current_player
    if depth == 0 or any(len(state.hands[p]) == 0 for p in range(3)):
        return evaluate_defensive(state, ai_player), None
    moves = get_legal_moves(state, current)
    if current == ai_player:
        best_score, best_move = float('-inf'), moves[0]
        for move in moves:
            score, _ = minimax(apply_move(state, current, move), depth - 1, ai_player)
            if score > best_score:
                best_score, best_move = score, move
        return best_score, best_move
    else:
        best_score, best_move = float('inf'), moves[0]
        for move in moves:
            score, _ = minimax(apply_move(state, current, move), depth - 1, ai_player)
            if score < best_score:
                best_score, best_move = score, move
        return best_score, best_move


def expectimax(state, depth, ai_player):
    #Expectimax: MAX for ai_player, CHANCE for opponents
    current = state.current_player
    if depth == 0 or any(len(state.hands[p]) == 0 for p in range(3)):
        return evaluate_offensive(state, ai_player), None
    moves = get_legal_moves(state, current)
    if current == ai_player:
        best_score, best_move = float('-inf'), moves[0]
        for move in moves:
            score, _ = expectimax(apply_move(state, current, move), depth - 1, ai_player)
            if score > best_score:
                best_score, best_move = score, move
        return best_score, best_move
    else:
        if 'draw' in moves:
            if state.deck:
                card_types = Counter(str(c) for c in state.deck)
                sampled = card_types.most_common(5)
                sampled_total = sum(cnt for _, cnt in sampled)
                total_score = 0.0
                for card_str, count in sampled:
                    card_obj = next(c for c in state.deck if str(c) == card_str)
                    prob = count / sampled_total
                    ds = state.clone()
                    ds.hands[current].append(card_obj)
                    ds.current_player = (current + 1) % 3
                    score, _ = expectimax(ds, depth - 1, ai_player)
                    total_score += prob * score
                return total_score, 'draw'
            else:
                score, _ = expectimax(apply_move(state, current, 'draw'), depth - 1, ai_player)
                return score, 'draw'
        else:
            total = sum(expectimax(apply_move(state, current, m), depth - 1, ai_player)[0] for m in moves)
            return total / len(moves), moves[0]
