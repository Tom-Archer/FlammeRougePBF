import math
import os
import pickle
import random
from enum import Enum

# Determines whether decks are kept secret in the Energy and Movement Phases
KEEP_DECK_SECRET = False

class Format(Enum):
    BBCODE = 1
    DISCOURSE = 2
    
# Determines the phase output format
FORMAT = Format.DISCOURSE

class Decklist:
    def __init__(self, cards):
        self.energy_pile = list(map(str, cards))
        self.recycle_pile = []
        self.discard_pile = []
        self.drawn_cards =  []
        self.message = ""
        random.shuffle(self.energy_pile)
        
    def add_exhaustion(self):
        # Add an exhaustion card to the recycle pile
        self.recycle_pile.append("e2")
        
    def _shuffle_recycle(self):
        # Shuffle the recycle pile into the draw pile
        self.energy_pile = self.recycle_pile
        self.recycle_pile = []
        random.shuffle(self.energy_pile)
        
    def shuffle_deck(self, include_discard = True):
        # Shuffle deck (and optionally the discard pile)
        if include_discard:
            self.energy_pile += self.recycle_pile + self.drawn_cards + self.discard_pile
            self.discard_pile = []
        else:
            self.energy_pile += self.recycle_pile + self.drawn_cards
        self.recycle_pile = []
        self.drawn_cards = []
        random.shuffle(self.energy_pile)
        
    def draw_cards(self):
        # Prevent drawing cards if hand is not empty
        if len(self.drawn_cards) > 0:
            return
        
        # If energy pile has more than 4 cards, take 4 cards from the top
        # If player has 4 cards (or fewer) remaining return all the cards
        # Else, shuffle the recycle pile and draw
        self.drawn_cards = []
        self.message = ""
        
        if len(self.energy_pile) >= 4:
            for i in range(0,4):
                self.drawn_cards.append(self.energy_pile.pop(0))
        elif len(self.energy_pile) + len(self.recycle_pile) == 0:
            self.message = "(No cards left in deck)"
            self.drawn_cards = ['e2']
        elif len(self.energy_pile) + len(self.recycle_pile) < 4:
            self.message = "(4 or fewer cards left in deck)"
            self.drawn_cards = self.energy_pile + self.recycle_pile
            self.energy_pile = []
            self.recycle_pile = []
        else:
            self.message = "(Deck got shuffled)"
            self.drawn_cards = self.energy_pile
            self._shuffle_recycle()
            for i in range(0,4-len(self.drawn_cards)):
                self.drawn_cards.append(self.energy_pile.pop(0))
                    
    def perform_end_of_stage_actions(self):
        self.message = ""
        # Remove any exhaustion cards in the discard pile
        self.discard_pile = [c for c in self.discard_pile if c != "e2"]
        # Move all cards back into the energy_pile
        self.shuffle_deck(True)
        # Remove half of the exhaustion cards
        self.energy_pile.sort()
        ex_count = self.energy_pile.count("e2")
        ex_count_end = math.ceil(ex_count / 2.0)
        for i in range(0, ex_count - ex_count_end):
            self.energy_pile.remove("e2")
        # Shuffle the deck
        random.shuffle(self.energy_pile)
        return (ex_count, ex_count_end)
        
    def play_card(self, card_name):
        # Discard the played card and recycle the remaining drawn cards
        if card_name in self.drawn_cards:
            self.discard_pile.append(card_name)
            self.drawn_cards.remove(card_name)
            self.recycle_pile += self.drawn_cards
            self.drawn_cards = []
    
    def get_last_cards_played(self):
        # Return the last played cards
        return list(reversed(self.discard_pile))
            
    def get_deck_list(self):
        return sorted(self.energy_pile + self.recycle_pile)
    
    def __str__(self):
        return "Hand: {0} - Energy: {1} - Recycle: {2} - Discard: {3}\n".format(",".join(self.drawn_cards), ",".join(self.energy_pile), ",".join(self.recycle_pile), ",".join(self.discard_pile))
    
class Rider(Decklist):
    def __init__(self, name, short_name, deck_list):
        super().__init__(deck_list)
        self.name = name
        self.short_name = short_name
        self.in_breakaway = False
        self.finished_stage = False
    
    def perform_end_of_stage_actions(self):
        # Reset breakaway flag
        self.in_breakaway = False
        # Reset finished flag
        self.finished_stage = False
        return super().perform_end_of_stage_actions()
        
    def __str__(self):
        return super().__str__()
        
class Team:
    def __init__(self, name, player, colour):
        self.name = name
        self.player = player
        self.colour = colour
        self.riders = {}
        self.riders["R"] = Rider("Rouleur", "R", [3,3,3,4,4,4,5,5,5,6,6,6,7,7,7])
        self.riders["S"] = Rider("Sprinteur", "S", [2,2,2,3,3,3,4,4,4,5,5,5,9,9,9])

    def play_s(self, play_string):
        # Take a shorthand string and play those cards
        # eg. "s5 r4"
        rider_strings = play_string.split(' ')
        for rider_string in rider_strings:
            if rider_string[0].upper() in self.riders:
                rider = self.riders[rider_string[0].upper()]
                rider.play_card(rider_string[1:])
        
    def add_s(self, add_string):
        # Take a shorthand string and add exhaustion to those riders
        # eg. "s r"
        rider_strings = add_string.split(' ')
        for rider_string in rider_strings:
            if rider_string[0].upper() in self.riders:
                rider = self.riders[rider_string[0].upper()]
                rider.add_exhaustion()
        
    def __str__(self):
        display_string = "{0} ({1})\n".format(self.name, self.player)
        for short, rider in self.riders.items():
            if rider.in_breakaway:
                display_string += "{0} (B):\n{1}\n".format(rider.name, rider)
            else:
                display_string += "{0}:\n{1}\n".format(rider.name, rider)
        return display_string
        
class Stage:
    def __init__(self, name=""):
        self.name = name
        self.team_dict = {}
        self.turn_number = 0
        self.bid_number = 0
        self.breakaway_started = False;
        
    def from_stage(self, previous_stage):
        # Take the result of the previous stage and create this new stage
        display_string = "[b][u]Exhaustion cards carried over to {0}[/u][/b]\n".format(self.name)
        
        self.team_dict = previous_stage.team_dict
        # Sort out all the decks
        for team_name, team in self.team_dict.items():
            
            if FORMAT == Format.BBCODE:
                display_string += "[COLOR={0}]".format(team.colour)
            
            for short, rider in team.riders.items():
                (start, finish) = rider.perform_end_of_stage_actions()
                display_string += "{0} {1}: {2} -> {3}\n".format(team_name, rider.name, start, finish)
                
            if FORMAT == Format.BBCODE:
                display_string += "[/COLOR]"
                
        return display_string
        
    def add_team(self, team_name, team_player, team_colour):
        self.team_dict[team_name] = Team(team_name, team_player, team_colour)
    
    def get_team(self, team_name):
        return self.team_dict[team_name]

    def perform_breakaway_energy_phase(self):
        # Perform breakaway
        self.breakaway_started = True;
        self.bid_number += 1
        
        # Draw cards for all riders in breakaway
        for team_name, team in self.team_dict.items():
            for short, rider in team.riders.items():
                if rider.in_breakaway:
                    rider.draw_cards()

    def output_breakaway_energy_phase(self):
        # Outputs the last breakaway energy phase
        display_string = "[b][u]Breakaway Turn {0} - Energy Phase[/u][/b]\n\n".format(self.bid_number)
        
        display_string = self._output_energy_phase(display_string, True)
        
        return display_string
    
    def output_breakaway_bid_phase(self):
        # Outputs the last breakaway bid phase
        display_string = "[b][u]Breakaway Turn {0} - Bid Phase[/u][/b]\n\n".format(self.bid_number)
        
        display_string = self._output_movement_phase(display_string, True)
            
        return display_string
        
    def perform_energy_phase(self):
        self.breakaway_started = False;
        
        # Performs card draws for each rider
        self.turn_number += 1
        for team_name, team in self.team_dict.items():
            for short, rider in team.riders.items():
                if not rider.finished_stage:
                    rider.draw_cards()

    def output_energy_phase(self):
        # Outputs the last energy phase
        display_string = "[b][u]Turn {0} - Energy Phase[/u][/b]\n\n".format(self.turn_number)
        
        display_string = self._output_energy_phase(display_string, False)

        return display_string
    
    def output_movement_phase(self):
        # Outputs the last movement phase
        display_string = "[b][u]Turn {0} - Movement Phase[/u][/b]\n".format(self.turn_number)
        display_string += "Numbers in brackets are how many spaces the cyclist actually moved (if blocked or because of ascents/descents)\n\n"
        
        display_string = self._output_movement_phase(display_string, False)
        
        display_string += "Positions (before slipstream):\n"
        display_string += "**INSERT IMAGE HERE**\n\n"
        
        display_string += "[b][u]Turn {0} - End Phase[/u][/b]\n".format(self.turn_number)
        display_string += "Positions (after slipstream):\n"
        display_string += "**INSERT IMAGE HERE**\n\n"
        display_string += "[b]Exhaustion card(s):[/b]\n"
        	
        return display_string

    def _output_energy_phase(self, display_string, breakaway = False):
        for team_name, team in sorted(list(self.team_dict.items())):
    
            if FORMAT == Format.DISCOURSE:
                display_string += "[b]{0} ({1})[/b]\n".format(team.name, team.player)
            else:
                display_string += "[COLOR={0}][b]{1} ({2})[/b][/COLOR]\n".format(team.colour, team.name, team.player)
            
            for short, rider in sorted(list(team.riders.items())):
                
                if (not rider.finished_stage) and ((not breakaway) or (breakaway and rider.in_breakaway)):
                    if FORMAT == Format.DISCOURSE:
                        display_string += "[details=\"{0}: {1}\"]\n".format(rider.name, rider.message)
                        if KEEP_DECK_SECRET:
                            display_string += "[b]Hand: {0}[/b] - Recycle: {1}\n".format(",".join(sorted(rider.drawn_cards)), ",".join(sorted(rider.recycle_pile)))
                        else:
                            display_string += "[b]Hand: {0}[/b] - Energy: {1} - Recycle: {2}\n".format(",".join(sorted(rider.drawn_cards)), ",".join(sorted(rider.energy_pile)), ",".join(sorted(rider.recycle_pile)))
                        display_string += "[/details]\n"
                    else:
                        display_string += "[COLOR={0}]{1}: {2}[/COLOR]\n".format(team.colour, rider.name, rider.message)
                        if KEEP_DECK_SECRET:
                            display_string += "[o][b]Hand: {0}[/b] - Recycle: {1}[/o]\n".format(",".join(sorted(rider.drawn_cards))), ",".join(sorted(rider.recycle_pile))
                        else:
                            display_string += "[o][b]Hand: {0}[/b] - Energy: {1} - Recycle: {2}[/o]\n".format(",".join(sorted(rider.drawn_cards)), ",".join(sorted(rider.energy_pile)), ",".join(sorted(rider.recycle_pile)))
                    
                    display_string += "\n"
            
        return display_string
        
    def _output_movement_phase(self, display_string, breakaway = False):
        for team_name, team in sorted(list(self.team_dict.items())):
        
            if FORMAT == Format.DISCOURSE:
                display_string += "[b]{0} ({1})[/b]\n".format(team.name, team.player)
            else:
                display_string += "[COLOR={0}][b]{1} ({2})[/b]\n".format(team.colour, team.name, team.player)
            
            for short, rider in sorted(list(team.riders.items())):
            
                if (not rider.finished_stage) and ((not breakaway) or (breakaway and rider.in_breakaway)):
                    cards_played = rider.get_last_cards_played()
                    rider_card = None
                    if len(cards_played) > 0:
                        rider_card = cards_played[0]
                    rider_deck = rider.get_deck_list()
                    
                    display_string += "{0}:\n".format(rider.name)
                    if KEEP_DECK_SECRET:
                        display_string += "[b]Card Played: {0}[/b]\n".format(str(rider_card))
                    elif breakaway:
                        if self.bid_number == 1:
                            display_string += "[b]Card Played: {0}[/b]\n".format(str(rider_card))
                        elif self.bid_number == 2:
                            if len(cards_played) < 2:
                                display_string += "[b]Card Played: None[/b]\n"   
                            else:
                                first_bid = cards_played[1]
                                display_string += "[b]Card Played: {0}[{1}][/b]\n".format(str(rider_card), int(rider_card) + int(first_bid))
                    else:
                        display_string += "[b]Card Played: {0}[/b] - Deck: {1}\n".format(str(rider_card), ",".join(rider_deck))
                
            if FORMAT == Format.DISCOURSE:
                display_string += "\n\n"
            else:
                display_string += "[/COLOR]\n\n"		
        
        return display_string
        
    def __str__(self):
        display_string = "{0}\n".format(self.name)
        display_string += "Bid Number: {0}\n".format(self.bid_number)
        display_string += "Turn Number: {0}\n".format(self.turn_number)
        for team_name, team in self.team_dict.items():
            display_string +=  "{0}\n".format(team)
        return display_string
        
def load_stage(filename):
    with open(filename, 'rb') as f:
        stage = pickle.load(f)	
        return stage
        
def store_stage(filename, stage):
    with open(filename, 'wb') as f:
        pickle.dump(stage, f)