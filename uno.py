import random
from collections import Counter
import tkinter as tk
from tkinter import font as tkfont


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

CARD_COLORS = {
    'Red': '#D32F2F', 'Blue': '#1565C0', 'Green': '#2E7D32', 'Yellow': '#F9A825',
}
BG      = '#1B5E20'
BG_DARK = '#0D3B0F'
TITLE_C = '#FFD600'
HDR_C   = '#FFEB3B'
TXT_C   = '#E8F5E9'
LOG_BG  = '#263238'
CW, CH  = 58, 82  # Card dimensions


class UnoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("UNO Game AI - Assignment 2")
        self.root.configure(bg=BG)
        self.root.geometry("1060x660")
        self.root.minsize(850, 550)

        self.state = None
        self.turn = 0
        self.game_over = False
        self.sim_mode = True
        self.auto_playing = False
        self.waiting_human = False

        self.f_title   = tkfont.Font(family="Consolas", size=20, weight="bold")
        self.f_header  = tkfont.Font(family="Consolas", size=10, weight="bold")
        self.f_card    = tkfont.Font(family="Arial", size=16, weight="bold")
        self.f_card_sm = tkfont.Font(family="Arial", size=7, weight="bold")
        self.f_btn     = tkfont.Font(family="Consolas", size=10, weight="bold")
        self.f_log     = tkfont.Font(family="Consolas", size=9)
        self.f_info    = tkfont.Font(family="Consolas", size=9)

        self._build_ui()
        self.new_game()

    def _build_ui(self):
        #TITLE + MODE
        top_bar = tk.Frame(self.root, bg=BG)
        top_bar.pack(fill=tk.X, padx=10, pady=(6, 2))

        tk.Label(top_bar, text="UNO  GAME  AI", font=self.f_title,
                 fg=TITLE_C, bg=BG).pack(side=tk.LEFT, padx=(10, 30))

        tk.Label(top_bar, text="P3 Mode:", font=self.f_info,
                 fg=TXT_C, bg=BG).pack(side=tk.LEFT)
        self.mode_var = tk.StringVar(value="simulation")
        for txt, val in [("Simulation", "simulation"), ("Manual", "manual")]:
            tk.Radiobutton(top_bar, text=txt, variable=self.mode_var, value=val,
                           font=self.f_info, fg=TXT_C, bg=BG, selectcolor=BG_DARK,
                           activebackground=BG, activeforeground=TITLE_C,
                           command=self._mode_changed).pack(side=tk.LEFT, padx=3)

        # TOP CARD + DECK
        tc_frame = tk.Frame(self.root, bg=BG)
        tc_frame.pack(pady=(2, 2))
        tk.Label(tc_frame, text="TOP CARD", font=self.f_header,
                 fg='#EF5350', bg=BG).pack(side=tk.LEFT, padx=(0, 5))
        self.cv_top = tk.Canvas(tc_frame, width=62, height=86, bg=BG, highlightthickness=0)
        self.cv_top.pack(side=tk.LEFT)
        self.lbl_deck = tk.Label(tc_frame, text="", font=self.f_info, fg=TXT_C, bg=BG)
        self.lbl_deck.pack(side=tk.LEFT, padx=(10, 0))

        # PLAYER AREAS 
        pf = tk.Frame(self.root, bg=BG)
        pf.pack(fill=tk.X, padx=10, pady=(2, 2))
        pf.columnconfigure(0, weight=1)
        pf.columnconfigure(1, weight=1)
        pf.columnconfigure(2, weight=1)

        self.p_frames = []
        self.p_canvas = []
        self.p_labels = []
        titles = [" P1  Minimax  Defensive ", " P2  Expectimax  Offensive ",
                  " P3  Manual / Simulation "]
        for i in range(3):
            lf = tk.LabelFrame(pf, text=titles[i], font=self.f_header,
                               fg=HDR_C, bg=BG_DARK, bd=2, relief=tk.GROOVE)
            lf.grid(row=0, column=i, sticky='nsew',
                    padx=(0 if i == 0 else 4, 0 if i == 2 else 4), ipady=2)
            cv = tk.Canvas(lf, height=110, bg=BG_DARK, highlightthickness=0)
            cv.pack(fill=tk.X, padx=4, pady=3)
            lb = tk.Label(lf, text="5 cards", font=self.f_info, fg=TXT_C, bg=BG_DARK)
            lb.pack()
            self.p_frames.append(lf)
            self.p_canvas.append(cv)
            self.p_labels.append(lb)

        # BUTTONS
        bf = tk.Frame(self.root, bg=BG)
        bf.pack(pady=(6, 4))


        self.btn_auto = tk.Button(bf, text="Auto-Play", font=self.f_btn,
                                  bg='#1E88E5', fg='white', relief=tk.FLAT,
                                  padx=18, pady=4, cursor='hand2',
                                  activebackground='#1565C0', command=self.toggle_auto)
        self.btn_auto.pack(side=tk.LEFT, padx=6)

        self.btn_new = tk.Button(bf, text="New Game", font=self.f_btn,
                                 bg='#43A047', fg='white', relief=tk.FLAT,
                                 padx=18, pady=4, cursor='hand2',
                                 activebackground='#2E7D32', command=self.new_game)
        self.btn_new.pack(side=tk.LEFT, padx=6)

        self.btn_draw = tk.Button(bf, text="Draw Card", font=self.f_btn,
                                  bg='#FF8F00', fg='white', relief=tk.FLAT,
                                  padx=18, pady=4, cursor='hand2',
                                  activebackground='#E65100', command=self._human_draw)
        self.btn_draw.pack(side=tk.LEFT, padx=6)
        self.btn_draw.config(state=tk.DISABLED)  

        # GAME LOG
        tk.Label(self.root, text="Game Log", font=self.f_header,
                 fg=TXT_C, bg=BG).pack(pady=(0, 1))
        lf2 = tk.Frame(self.root, bg=LOG_BG)
        lf2.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))
        self.log = tk.Text(lf2, height=6, bg=LOG_BG, fg='#B2DFDB',
                           font=self.f_log, wrap=tk.WORD, bd=0,
                           padx=8, pady=6, state=tk.DISABLED)
        sb = tk.Scrollbar(lf2, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.log.tag_configure('p1', foreground='#EF9A9A')
        self.log.tag_configure('p2', foreground='#90CAF9')
        self.log.tag_configure('p3', foreground='#A5D6A7')
        self.log.tag_configure('sys', foreground='#FFD54F')
        self.log.tag_configure('win', foreground='#FFD600',
                               font=tkfont.Font(family="Consolas", size=11, weight="bold"))
    
    # CARD DRAWING 
    def _draw_card(self, canvas, x, y, card, w=CW, h=CH, clickable=False, idx=None):
        bg_c = CARD_COLORS.get(card.color, '#D32F2F')
        r = 7
        ids = []
        ids.append(canvas.create_rectangle(x+r, y, x+w-r, y+h, fill=bg_c, outline='#FFF', width=1))
        ids.append(canvas.create_rectangle(x, y+r, x+w, y+h-r, fill=bg_c, outline='#FFF', width=1))
        for cx2, cy2 in [(x, y), (x+w-2*r, y), (x, y+h-2*r), (x+w-2*r, y+h-2*r)]:
            ids.append(canvas.create_oval(cx2, cy2, cx2+2*r, cy2+2*r, fill=bg_c, outline='#FFF', width=1))
        ids.append(canvas.create_rectangle(x+3, y+3, x+w-3, y+h-3, fill=bg_c, outline=''))
        ow, oh = w*0.6, h*0.42
        ox, oy = x+(w-ow)/2, y+(h-oh)/2
        ids.append(canvas.create_oval(ox, oy, ox+ow, oy+oh, fill='white', outline=''))
        txt = 'S' if card.is_skip else card.value
        ids.append(canvas.create_text(x+w/2, y+h/2, text=txt, font=self.f_card, fill=bg_c))
        ids.append(canvas.create_text(x+10, y+12, text=txt, font=self.f_card_sm, fill='white'))
        ids.append(canvas.create_text(x+w-10, y+h-12, text=txt, font=self.f_card_sm, fill='white'))
        if clickable and idx is not None:
            for item_id in ids:
                canvas.tag_bind(item_id, '<Button-1>', lambda e, i=idx: self._human_card(i))

    def _render_hand(self, canvas, cards, clickable=False, legal_idx=None):
        canvas.delete("all")
        if not cards:
            canvas.create_text(150, 50, text="No cards!", font=self.f_info, fill=TXT_C)
            return
        canvas.update_idletasks()
        cw_total = canvas.winfo_width() or 300
        n = len(cards)
        spacing = min(CW + 6, max(20, (cw_total - 16 - CW) // max(n - 1, 1)))
        start_x = max(8, (cw_total - CW - (n - 1) * spacing) // 2)
        for i, card in enumerate(cards):
            click = clickable and (legal_idx is None or i in legal_idx)
            self._draw_card(canvas, start_x + i * spacing, 8, card, clickable=click, idx=i)

    #  REFRESH 
    def _refresh(self):
        if not self.state:
            return
        self.cv_top.delete("all")
        self._draw_card(self.cv_top, 2, 2, self.state.top_card, w=58, h=82)
        self.lbl_deck.config(text=f"Deck: {len(self.state.deck)} cards remaining")

        for p in range(3):
            cards = self.state.hands[p]
            if p == 2 and self.waiting_human:
                legal = get_legal_moves(self.state, 2)
                if legal != ['draw']:
                    legal_idx = {i for i, c in enumerate(cards) if c in legal}
                    self._render_hand(self.p_canvas[p], cards, clickable=True, legal_idx=legal_idx)
                else:
                    self._render_hand(self.p_canvas[p], cards)
            else:
                self._render_hand(self.p_canvas[p], cards)
            self.p_labels[p].config(text=f"{len(cards)} cards")

        for p in range(3):
            if p == self.state.current_player and not self.game_over:
                self.p_frames[p].config(highlightbackground=TITLE_C, highlightthickness=3)
            else:
                self.p_frames[p].config(highlightthickness=0)

    def _log(self, msg, tag='sys'):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, msg + "\n", tag)
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def _enable_draw_btn(self):
        #Enable the Draw Card button (orange, clickable)."""
        self.btn_draw.config(state=tk.NORMAL, bg='#FF8F00')

    def _disable_draw_btn(self):
        #Disable the Draw Card button (greyed out)."""
        self.btn_draw.config(state=tk.DISABLED, bg='#666666')

    def _mode_changed(self):
        self.sim_mode = (self.mode_var.get() == "simulation")
        self._log(f"Mode -> {'Simulation' if self.sim_mode else 'Manual'}", 'sys')

    # NEW GAME
    def new_game(self):
        self.auto_playing = False
        self.btn_auto.config(text="Auto-Play", bg='#1E88E5')
        self.game_over = False
        self.waiting_human = False
        self.turn = 0
        self.consecutive_passes = 0
        self.state = initialize_game()
        self.sim_mode = (self.mode_var.get() == "simulation")
        self._disable_draw_btn()
        self.log.config(state=tk.NORMAL)
        self.log.delete(1.0, tk.END)
        self.log.config(state=tk.DISABLED)
        mode_s = "Simulation" if self.sim_mode else "Manual"
        self._log(f"=== New Game  (P3: {mode_s}) ===", 'sys')
        self._log(f"Top card: {self.state.top_card}   Deck: {len(self.state.deck)}", 'sys')
        self._refresh()
        if not self.sim_mode:
            # Manual mode: auto-run AI turns until P3's turn
            self.root.after(300, self._run_until_human)

    def _run_until_human(self):
        #Auto-run AI turns until it's P3's turn in manual mode.
        if self.game_over or self.waiting_human:
            return
        current = self.state.current_player
        if current == 2:
            # It's P3's turn — prompt human
            self._prompt_human()
            return
        # Run one AI turn
        self.next_turn()

    def _prompt_human(self):
        #Prompt P3 to play in manual mode.
        self.turn += 1
        self.waiting_human = True
        legal = get_legal_moves(self.state, 2)
        if legal == ['draw']:
            self._log(f"Turn {self.turn}: P3 -- No valid cards! Click 'Draw Card'.", 'p3')
            self._enable_draw_btn()
        else:
            self._log(f"Turn {self.turn}: P3 -- Click a card to play.", 'p3')
            self._disable_draw_btn()
        self._refresh()

    # NEXT TURN 
    def next_turn(self):
        if self.game_over:
            self._log("Game over! Click 'New Game'.", 'sys')
            return
        if self.waiting_human:
            self._log("Your turn! Click a card to play or 'Draw Card'.", 'sys')
            return

        current = self.state.current_player

        # If it's P3's turn in manual mode, prompt immediately
        if current == 2 and not self.sim_mode:
            self._prompt_human()
            return

        self.turn += 1
        tag = ['p1', 'p2', 'p3'][current]

        # AI TURN 
        if current == 0:
            score, move = minimax(self.state, 2, 0)
            info = f"[Minimax] Score: {score}"
        elif current == 1:
            score, move = expectimax(self.state, 3, 1)
            info = f"[Expectimax] Score: {score:.1f}"
        else:
            score, move = minimax(self.state, 2, 2)
            info = f"[Minimax-Sim] Score: {score}"

        # APPLY MOVE 
        pn = f"P{current + 1}"
        if move == 'draw':
            had_cards = len(self.state.hands[current])
            self.state = apply_move(self.state, current, move)
            now_cards = len(self.state.hands[current])
            if now_cards > had_cards:
                new_card = self.state.hands[current][-1]
                self._log(f"Turn {self.turn}: {pn} no valid card -> draws {new_card}.  {info}", tag)
                self.consecutive_passes = 0
            else:
                self._log(f"Turn {self.turn}: {pn} no valid card & deck empty -> passes.  {info}", tag)
                self.consecutive_passes += 1
        else:
            self._log(f"Turn {self.turn}: {pn} plays {move}.  {info}", tag)
            if move.is_skip:
                skipped = (current + 1) % 3
                self._log(f"  >> SKIP! P{skipped + 1} loses their turn!", 'sys')
            self.state = apply_move(self.state, current, move)
            self.consecutive_passes = 0

        self._refresh()
        if self._check_win():
            return
        if self.consecutive_passes >= 3:
            self._end_stalemate()
            return

        # After AI turn: if next is P3 manual, auto-prompt them
        if self.state.current_player == 2 and not self.sim_mode:
            self.root.after(200, self._prompt_human)
            return

        # In manual mode, keep running AI turns automatically
        if not self.sim_mode and not self.game_over:
            self.root.after(300, self._run_until_human)
            return

        if self.auto_playing and not self.game_over:
            self.root.after(350, self.next_turn)



