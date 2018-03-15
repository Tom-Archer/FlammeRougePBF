from flammerouge import *

def test_stage():
	# Stage Setup
	stage = Stage("Stage #1")
	stage.add_team("Alice (Red)",  "#FF0000")
	stage.add_team("Bob (Blue)", "#0000FF")

	alice = stage.get_team("Alice (Red)")
	bob = stage.get_team("Bob (Blue)")

	print(stage)

	# Breakaway Phase 1
	stage.perform_breakaway_energy_phase()
	print(stage.output_breakaway_energy_phase())
	alice.riders["R"].in_breakaway = True
	bob.riders["S"].in_breakaway = True
	alice.play_s("r"+alice.riders["R"].drawn_cards[0])
	bob.play_s("s"+bob.riders["S"].drawn_cards[0])
	print(stage.output_breakaway_bid_phase())

	print(stage)

	# Breakaway Phase 2
	stage.perform_breakaway_energy_phase()
	print(stage.output_breakaway_energy_phase())
	alice.play_s("r"+alice.riders["R"].drawn_cards[0])
	bob.play_s("s"+bob.riders["S"].drawn_cards[0])
	print(stage.output_breakaway_bid_phase())

	print(stage)

	alice.add_s("r r")
	# assume alice won
	alice.riders["R"].shuffle_deck(False)
	alice.riders["S"].shuffle_deck(True)
	bob.riders["R"].shuffle_deck(True)
	bob.riders["S"].shuffle_deck(True)

	print(stage)

	# Turn 1
	stage.perform_energy_phase()
	
	print(stage)
	
	print(stage.output_energy_phase())
	
	alice.play_s("r{0} s{1}".format(alice.riders["R"].drawn_cards[0],alice.riders["S"].drawn_cards[0]))
	bob.play_s("r{0} s{1}".format(bob.riders["R"].drawn_cards[0],bob.riders["S"].drawn_cards[0]))
	alice.add_s("r")
	
	print(stage.output_movement_phase())
	
	print(stage)
	
	stage2 = Stage("Stage #2")
	stage2.from_stage(stage)
	
	print(stage2)
