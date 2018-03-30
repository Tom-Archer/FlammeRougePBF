from flask import Flask, render_template, render_template_string, jsonify, make_response, redirect, url_for
from flammerouge import *

app = Flask(__name__)

phase_text = ""
stage = Stage("Stage Name")
stage.add_team("Team 1","#0000FF")
stage.add_team("Team 2","#FF0000")
stage.breakaway = False

# Routes
# ======
@app.route("/")
def root(): 
    return render_stage(stage)

@app.route("/winner/<string:team_name>/<string:short>/")
def winner(team_name, short):
    team = stage.get_team(team_name)
    # Add two exhaustion
    team.add_s(short+" "+short)
    # Shuffle energy+recycle
    team.riders[short].shuffle_deck(False)
    team.riders[short].in_breakaway = False
    store_phase("breakaway_"+str(stage.bid_number)+"_end")
    
    return redirect(url_for('root'))

@app.route("/loser/<string:team_name>/<string:short>/")
def loser(team_name, short):
    team = stage.get_team(team_name)
    # Shuffle deck
    team.riders[short].shuffle_deck(True)
    team.riders[short].in_breakaway = False
    store_phase("breakaway_"+str(stage.bid_number)+"_end")
    
    return redirect(url_for('root'))

@app.route("/exhaustion/<string:team_name>/<string:short>/")
def exhaustion(team_name, short):
    team = stage.get_team(team_name)
    team.add_s(short)
    store_phase(str(stage.turn_number)+"_end")
    # update text?
    return redirect(url_for('root'))

@app.route("/finished/<string:team_name>/<string:short>/")
def finished(team_name, short):
    team = stage.get_team(team_name)
    team.riders[short].finished_stage = True
    return redirect(url_for('root'))

@app.route("/play/<string:team_name>/<string:short>/<string:play>")
def play(team_name, short, play):
    team = stage.get_team(team_name)
    team.play_s(short+play)
    
    if stage.breakaway:
        store_phase("breakaway_"+str(stage.bid_number)+"_movement")
        set_phase_text(stage.output_breakaway_bid_phase())
    else:   
        store_phase(str(stage.turn_number)+"_movement")
        set_phase_text(stage.output_movement_phase())
    
    return redirect(url_for('root'))

@app.route("/in_breakaway/<string:team_name>/<string:short>")
def in_breakaway(team_name, short):
    team = stage.get_team(team_name)
    rider = team.riders[short]
    rider.in_breakaway = True
    
    return redirect(url_for('root'))

@app.route("/breakaway")
def breakaway():
    if not stage == None:
        # Enable the rider selection
        if not stage.breakaway:
            stage.breakaway = True;
        else:
            stage.perform_breakaway_energy_phase()
            store_phase("breakaway_"+str(stage.bid_number)+"_energy")
            set_phase_text(stage.output_breakaway_energy_phase())
    return redirect(url_for('root'))

@app.route("/energy")
def energy():
    stage.breakaway = False
    stage.perform_energy_phase()
    store_phase(str(stage.turn_number)+"_energy")
    set_phase_text(stage.output_energy_phase())
    return redirect(url_for('root'))
        
# Helpers
# =======
def set_phase_text(text):
    global phase_text
    phase_text = text
    
def store_phase(filename):
    # Call in energy phases and after every movement
    # /Stage_Name/
    pass  
  
def can_display_in_breakaway(team_name):
    # If breakaway has been enabled, and no rider selected
    if not stage == None:
        if stage.breakaway and stage.bid_number == 0:
            team = stage.get_team(team_name)
            for rider in list(team.riders.values()):
                if rider.in_breakaway:
                    return False
            return True
    return False   

def can_display_winner_loser(rider):
    # If we are in a breakway, second round of bidding has occurred (all cards played)
    if not stage == None:
        if stage.bid_number == 2 and all_riders_have_played_cards(True) and rider.in_breakaway:
            return True
    return False

def all_teams_have_nominated_rider():
    if not stage == None:
        for team in list(stage.team_dict.values()):
            rider_found = False
            for rider in list(team.riders.values()):
                if rider.in_breakaway:
                    rider_found = True
            if not rider_found:
                return False
        return True
    return False

def no_teams_have_nominated_rider():
    if not stage == None:
        for team in list(stage.team_dict.values()):
            for rider in list(team.riders.values()):
                if rider.in_breakaway:
                    return False
        return True
    return False

def all_riders_have_played_cards(breakaway = False):
    if not stage == None:
        for team in list(stage.team_dict.values()):
            for rider in list(team.riders.values()):
                if breakaway:
                    if rider.in_breakaway:
                        if len(rider.drawn_cards) > 0:
                           return False
                else:
                    if len(rider.drawn_cards) > 0:
                        return False
        return True
    return False

def can_perform_breakaway():
    # If breakaway is already enabled:
    # 0 - Check each time has nominated a rider
    # 1 - Check each time has played a card
    # 2 - False
    if stage.breakaway:
        if stage.bid_number == 0:
            return all_teams_have_nominated_rider()
        elif stage.bid_number == 1:
            return all_riders_have_played_cards(True)
    # If we haven't started the stage or the breakaway
    elif stage.turn_number == 0 and stage.bid_number == 0:
        return True 
    return False

def can_display_rider_options(rider):
    if not stage == None:
        if stage.turn_number > 0 and all_riders_have_played_cards():
            if not rider.finished_stage:
                return True
    return False

def can_perform_energy():
    # Check we're not bidding
    if not stage == None:
        if not stage.breakaway:
            if all_riders_have_played_cards():
                return True
        elif stage.bid_number == 2:
            if all_riders_have_played_cards() and no_teams_have_nominated_rider():
                return True
    return False    
    

    
    
    









# Rendering Functions
# ========= =========
def render_stage(stage):
    teams = []
    for team_key in sorted(list(stage.team_dict.keys())):
        teams.append(render_team(stage.team_dict[team_key]))
    return render_template("stage.html", name=stage.name, teams=teams,
                           energy=can_perform_energy(),
                           breakaway=can_perform_breakaway(),
                           phase_text=phase_text)

def render_team(team):
    riders = []
    for rider_key in sorted(list(team.riders.keys())):
        riders.append(render_rider(team.riders[rider_key], team.name))
    
    return render_template("team.html", name=team.name, riders=riders, colour=team.colour)

def render_rider(rider, team_name):
    deck = [render_drawn_cards("Hand:", rider.drawn_cards, team_name, rider.short_name),
            render_cards("Energy:", rider.energy_pile),
            render_cards("Recycle:", rider.recycle_pile),
            render_cards("Discard:", rider.discard_pile)]
    
    message = rider.message;
    if rider.in_breakaway:
        message = "In Breakaway!"
    return render_template("rider.html", name=rider.name, deck=deck, team=team_name, short=rider.short_name, message=message,
                           winlose=can_display_winner_loser(rider),
                           breakaway=can_display_in_breakaway(team_name),
                           options=can_display_rider_options(rider))

def render_cards(pile_name, cards):
    return render_template("cards.html", name=pile_name, cards=cards)
    
def render_drawn_cards(pile_name, cards, team_name, short_name):
    return render_template("cards_drawn.html", name=pile_name, cards=cards, team=team_name, short=short_name)



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
    
    