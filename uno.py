import tkinter as tk
from tkinter import font as tkfont
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