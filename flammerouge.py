import math
import pickle
import random
from enum import Enum

# Determines whether decks are kept secret in the Energy and Movement Phases
KEEP_DECK_SECRET = False

class Format(Enum):
	BBCODE = 1
	DISCOURSE = 2
	
FORMAT = Format.DISCOURSE

class Decklist:
	def __init__(self, cards):
		self.energy_pile = list(map(str, cards))
		self.recycle_pile = []
		self.discard_pile = []
		self.drawn_cards =  []
		random.shuffle(self.energy_pile)
		
	def add_exhaustion(self):
		# Add an exhaustion card to the recycle pile
		self.recycle_pile.append("e2")
		
	def shuffle_recycle(self):
		# Shuffle the recycle pile into the draw pile
		self.energy_pile = self.recycle_pile
		self.recycle_pile = []
		random.shuffle(self.energy_pile)
		
	def draw_cards(self):
		# Take 4 cards from the top of the draw pile 
		# If player has 4 cards remaining just give them all the cards
		# Else, Shuffle the recycle pile if not enough cards
		self.drawn_cards = []
		message = ""
		
		if len(self.energy_pile) >= 4:
			for i in range(0,4):
				self.drawn_cards.append(self.energy_pile.pop(0))
		elif len(self.energy_pile) + len(self.recycle_pile) < 4:
			message = "(4 or fewer cards left in deck)"
			self.drawn_cards = self.energy_pile + self.recycle_pile
			self.energy_pile = []
			self.recycle_pile = []
		else:
			message = "(Deck got shuffled)"
			self.drawn_cards = self.energy_pile
			self.shuffle_recycle()
			for i in range(0,4-len(self.drawn_cards)):
				self.drawn_cards.append(self.energy_pile.pop(0))
			
		return (sorted(self.drawn_cards), message)
		
	def perform_end_of_stage_actions(self):
		# Remove any exhaustion cards in the discard pile
		self.discard_pile = [c for c in self.discard_pile if c != "e2"]
		# Merge the drawn_cards & recycle_pile into the energy_pile
		self.energy_pile += self.recycle_pile + self.drawn_cards + self.discard_pile
		self.recycle_pile = []
		self.drawn_cards = []
		self.discard_pile = []
		# Remove half of the exhaustion cards
		self.energy_pile.sort()
		ex_count = self.energy_pile.count("e2")
		for i in range(0, ex_count - math.ceil(ex_count / 2.0)):
			self.energy_pile.remove("e2")
		# Shuffle the deck
		random.shuffle(self.energy_pile)	
		
	def play_card(self, card_name):
		# Take the played card from the drawn cards and recycle the drawn cards
		if card_name in self.drawn_cards:
			self.discard_pile.append(card_name)
			self.drawn_cards.remove(card_name)
			self.recycle_pile += self.drawn_cards
			self.drawn_cards = []
		else:
			print("The played card {0} was not in the list of drawn cards!".format(card_name))
	
	def get_last_card_played(self):
		# Return the last played card
		if len(self.discard_pile) > 0:
			return self.discard_pile[-1]
		return None
			
	def get_deck_list(self):
		return sorted(self.energy_pile + self.recycle_pile)
	
	def __str__(self):
		# This gives the behind the scenes info
		return "Hand: {0} - Energy: {1} - Recycle: {2} - Discard: {3}\n".format(",".join(self.drawn_cards), ",".join(self.energy_pile), ",".join(self.recycle_pile), ",".join(self.discard_pile))
	
class Rider(Decklist):
	def __init__(self, name, short_name, deck_list):
		super().__init__(deck_list)
		self.name = name
		self.short_name = short_name
		
	def __str__(self):
		return super().__str__()
		
class Team:
	def __init__(self, name, colour):
		self.name = name
		self.colour = colour
		self.riders = []
		self.riders.append(Rider("Rouleur", "R", [3,3,3,4,4,4,5,5,5,6,6,6,7,7,7]))
		self.riders.append(Rider("Sprinteur", "S", [2,2,2,3,3,3,4,4,4,5,5,5,9,9,9]))

	def play_s(self, play_string):
		# Take a shorthand string and play those cards
		rider_strings = play_string.split(' ')
		for rider_string in rider_strings:
			for rider in self.riders:
				if rider_string[0].upper() == rider.short_name:
					rider.play_card(rider_string[1:])
					break
		
	def add_s(self, add_string):
		# Take a shorthand string and add exhaustion to those riders
		rider_strings = add_string.split(' ')
		for rider_string in rider_strings:
			for rider in self.riders:
				if rider_string[0].upper() == rider.short_name:
					rider.add_exhaustion()
					break
		
	def __str__(self):
		display_string = "{0}\n".format(self.name)
		for rider in self.riders:
			display_string += "{0}:\n{1}\n".format(rider.name, rider)
		return display_string
		
class Stage:
	def __init__(self, name=""):
		self.name = name
		self.team_dict = {}
		self.turn_number = 0
		
	def from_stage(self, previous_stage):
		# Take the result of the previous stage and create this new stage
		self.team_dict = previous_stage.team_dict
		# Sort out all the decks
		for team_name in self.team_dict.keys():
			team = self.team_dict[team_name]
			for rider in team.riders:
				rider.perform_end_of_stage_actions()
		
	def add_team(self, team_name, team_colour):
		self.team_dict[team_name] = Team(team_name, team_colour)
	
	def get_team(self, team_name):
		return self.team_dict[team_name]
	
	def output_energy_phase(self):
		# Outputs the next energy phase
		self.turn_number += 1
		display_string = "[b][u]Turn {0} - Energy Phase[/u][/b]\n\n".format(self.turn_number)
		
		for team_name in self.team_dict.keys():
			
			team = self.team_dict[team_name]
			if FORMAT == Format.DISCOURSE:
				display_string += "[b]{0}[/b]\n".format(team.name)
			else:
				display_string += "[COLOR={0}][b]{1}[/b][/COLOR]\n".format(team.colour, team.name)
			
			for rider in team.riders:
				(rider_hand, rider_msg) = rider.draw_cards()
				(rider_energy, rider_recycle) = (rider.energy_pile, rider.recycle_pile)

				if FORMAT == Format.DISCOURSE:
					display_string += "[details=\"{0}: {1}\"]\n".format(rider.name, rider_msg)
					if KEEP_DECK_SECRET:
						display_string += "[b]Hand: {0}[/b] - Recycle: {1}\n".format(",".join(rider_hand), ",".join(rider_recycle))
					else:
						display_string += "[b]Hand: {0}[/b] - Energy: {1} - Recycle: {2}\n".format(",".join(rider_hand), ",".join(sorted(rider_energy)), ",".join(sorted(rider_recycle)))
					display_string += "[/details]\n"
				else:
					display_string += "[COLOR={0}]{1}: {2}[/COLOR]\n".format(team.colour, rider.name, rider_msg)
					if KEEP_DECK_SECRET:
						display_string += "[o][b]Hand: {0}[/b] - Recycle: {1}[/o]\n".format(",".join(rider_hand), ",".join(rider_recycle))
					else:
						display_string += "[o][b]Hand: {0}[/b] - Energy: {1} - Recycle: {2}[/o]\n".format(",".join(rider_hand), ",".join(sorted(rider_energy)), ",".join(sorted(rider_recycle)))
				
				display_string += "\n"

		with open("energy_{0}.txt".format(self.turn_number), 'w') as f:
			f.write(display_string)
		return display_string
		
	def output_movement_phase(self):
		# Outputs the last movement phase
		display_string = "[b][u]Turn {0} - Movement Phase[/u][/b]\n".format(self.turn_number)
		display_string += "Numbers in brackets are how many spaces the cyclist actually moved (if blocked or because of ascents/descents)\n\n"
		
		for team_name in self.team_dict.keys():
		
			team = self.team_dict[team_name]
			if FORMAT == Format.DISCOURSE:
				display_string += "[b]{0}[/b]\n".format(team.name)
			else:
				display_string += "[COLOR={0}][b]{1}[/b]\n".format(team.colour, team.name)
			
			for rider in team.riders:
				(rider_card, rider_deck) = (rider.get_last_card_played(), rider.get_deck_list())
				
				display_string += "{0}:\n".format(rider.name)
				if KEEP_DECK_SECRET:
					display_string += "[b]Card Played: {0}[/b]\n".format(str(rider_card))
				else:
					display_string += "[b]Card Played: {0}[/b] - Deck: {1}\n".format(str(rider_card), ",".join(rider_deck))
				
			if FORMAT == Format.DISCOURSE:
				display_string += "\n\n"
			else:
				display_string += "[/COLOR]\n\n"
		
		display_string += "Positions (before slipstream):\n"
		display_string += "**INSERT IMAGE HERE**\n\n"
		
		display_string += "[b][u]Turn {0} - End Phase[/u][/b]\n".format(self.turn_number)
		display_string += "Positions (after slipstream):\n"
		display_string += "**INSERT IMAGE HERE**\n\n"
		display_string += "[b]Exhaustion card(s):[/b]"
		
		with open("movement_{0}.txt".format(self.turn_number), 'w') as f:
			f.write(display_string)		
		return display_string

	def __str__(self):
		display_string = "{0}\n".format(self.name)
		for team_name in self.team_dict.keys():
			display_string +=  "{0}\n".format(self.team_dict[team_name])
		return display_string
		
def load_stage(filename):
	with open(filename, 'rb') as f:
		stage = pickle.load(f)	
		return stage
		
def store_stage(filename, stage):
	with open(filename, 'wb') as f:
		pickle.dump(stage, f)	
	
if __name__ == "__main__":

	stage = Stage("Stage #1")
	stage.add_team("Red",  "#FF0000")
	stage.add_team("Blue", "#0000FF")
	
	red_team = stage.get_team("Red") 
	blue_team = stage.get_team("Blue") 
	
	print(stage)
	print(stage.output_energy_phase())
	
	#red_team.riders[0].play_card(red_team.riders[0].drawn_cards[0])
	red_team.play_s("r"+red_team.riders[0].drawn_cards[0])
	red_team.add_s("r r r r")
	print(stage)
	print(stage.output_movement_phase())	
	
	#red_team.riders[0].discard_pile.append("e2")
	#red_team.riders[0].discard_pile.append("e2")
	#stage2 = Stage("Stage #2")
	#stage2.from_stage(stage)
	#print(stage2)
