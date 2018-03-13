import random
import pickle

# Determines whether decks are kept secret in the Energy and Movement Phases
KEEP_DECK_SECRET = False

class Decklist:
	def __init__(self, cards):
		self.energy_pile = list(map(str, cards))
		self.recycle_pile = []
		self.discard_pile = []
		self.drawn_cards =  []
		random.shuffle(self.energy_pile)
		
	def add_card(self, card_name):
		# Add a card to the recycle pile
		self.recycle_pile.append(str(card_name))
		
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
		return "Hand: {0} - Energy: {1} - Recycle: {2}\n".format(",".join(self.drawn_cards), ",".join(self.energy_pile), ",".join(self.recycle_pile))
	
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
		
	def __str__(self):
		display_string = "{0}\n".format(self.name)
		for rider in self.riders:
			display_string += "{0}:\n{1}\n".format(rider.name, rider)
		return display_string
		
class Stage:
	def __init__(self, name=""):
		self.name = name
		self.team_dict = {}
		
	def add_team(self, team_name, team_colour):
		self.team_dict[team_name] = Team(team_name, team_colour)
	
	def get_team(self, team_name):
		return self.team_dict[team_name]
	
	def output_next_turn(self):
		display_string = ""
		# Prints out the next round
		for team_name in self.team_dict.keys():
			
			team = self.team_dict[team_name]
			display_string += "[COLOR={0}][b]{1}[/b][/COLOR]\n".format(team.colour, team.name)
			
			for rider in team.riders:
				(rider_hand, rider_msg) = rider.draw_cards()
				(rider_energy, rider_recycle) = (rider.energy_pile, rider.recycle_pile)
				
				display_string += "[COLOR={0}]{1}: {2}[/COLOR]\n".format(team.colour, rider.name, rider_msg)
				if KEEP_DECK_SECRET:
					display_string += "[o][b]Hand: {0}[/b] - Recycle: {1}[/o]\n".format(",".join(rider_hand), ",".join(rider_recycle))
				else:
					display_string += "[o][b]Hand: {0}[/b] - Draw: {1} - Recycle: {2}[/o]\n".format(",".join(rider_hand), ",".join(sorted(rider_energy)), ",".join(sorted(rider_recycle)))
				
			display_string += "\n"

		return display_string
		
	def output_last_turn(self):
		display_string = ""
		# Prints out the last round of actions
		for team_name in self.team_dict.keys():
		
			team = self.team_dict[team_name]
			display_string += "[COLOR={0}][b]{1}[/b]\n".format(team.colour, team.name)
			
			for rider in team.riders:
				(rider_card, rider_deck) = (rider.get_last_card_played(), rider.get_deck_list())
				display_string += "{0}:\n".format(rider.name)
				if KEEP_DECK_SECRET:
					display_string += "[b]Card Played: {0}[/b]\n".format(str(rider_card))
				else:
					display_string += "[b]Card Played: {0}[/b] - Deck: {1}\n".format(str(rider_card), ",".join(rider_deck))
			display_string += "[/COLOR]\n\n"
				
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
	stage.add_team("Team1", "#FF0000")
	stage.add_team("Team2", "#00FF00")
	
	print(stage)
	print(stage.output_next_turn())
	print(stage)
	
	red_team = stage.get_team("Team1")
	#red_team.play_s("re2")
	red_team.riders[0].play_card(red_team.riders[0].drawn_cards[0])
	red_team.riders[0].add_card("e2")
	
	print(stage.output_last_turn())
	print(stage)

