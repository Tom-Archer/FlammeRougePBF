import os
from flask import Flask, render_template, redirect, url_for, request, jsonify
from flammerouge import *
from random import randint

app = Flask(__name__)

phase_text = ""
current_stage = None
last_exhaustion = []
stages_dir = "./stages/"

# Routes
# ======
@app.route("/")
def root():
    stage_name = None
    if not current_stage == None:
        stage_name = current_stage.name
    return render_template("stage_options.html", current_stage = stage_name)

@app.route("/stage")
def stage():
    # Displays current stage
    if not current_stage == None:
        return render_stage()
    return redirect(url_for('root'))

@app.route("/new_stage")
def new_stage():
    return render_template("new_stage.html")

@app.route("/create_stage", methods=['POST'])
def create_stage():
    global current_stage
    if request.method == 'POST':
        current_stage = Stage(request.form["stage_name"])
        
        for i in range(1,7):
            team_name = request.form["team_name_"+str(i)]
            team_colour = request.form["team_colour_"+str(i)]
            team_player = request.form["team_player_"+str(i)] 
            if not ((team_name == "") or (team_colour == "")):
                current_stage.add_team(team_name, team_player, team_colour)
        
        root = os.path.join(stages_dir, current_stage.name)
        create_folder_for_stage(root)
            
        # Store stage
        store_phase("created")
    return redirect(url_for('stage'))

@app.route("/new_stage_from")
def new_stage_from():
    return render_template("new_stage_from.html",
                           stage_name = current_stage.name, files=get_files_for_stage(current_stage.name))

@app.route("/create_stage_from", methods=['POST'])
def create_stage_from():
    global current_stage
    if request.method == 'POST':
        current_stage_name = request.form["stage_name"]
        stage_file = request.form["stage_file"]
        new_stage_name = request.form["new_stage_name"]
    
        if not new_stage_name == "":
            new_stage = Stage(new_stage_name)
            current_stage = load_stage(os.path.join(stages_dir, current_stage_name, stage_file))
            set_phase_text(new_stage.from_stage(current_stage))
            current_stage = new_stage
            
            create_folder_for_stage(os.path.join(stages_dir, new_stage_name))
            store_phase("created")
            
    return redirect(url_for('stage'))

@app.route("/view_stage_list")
def view_stage_list():
    # List all stages
    stages = get_stage_list()
    file_dict = {}
    for stage in stages:
        file_dict[stage] = get_files_for_stage(stage)
    return render_template("view_stages.html", stage_names=stages, files=file_dict)

@app.route("/load_stage_state", methods=['POST'])
def load_stage_state():
    global current_stage
    # load a selected stage
    if request.method == 'POST':
        stage_name = request.form["stage_name"]
        stage_file = request.form["stage_file"]
        path = os.path.join(stages_dir, stage_name, stage_file)

        if os.path.isfile(path):
            current_stage = load_stage(path)
            set_phase_text("")
    return redirect(url_for('stage'))

@app.route("/winner/<string:team_name>/<string:short>/")
def winner(team_name, short):
    team = current_stage.get_team(team_name)
    # Add two exhaustion
    team.add_s(short+" "+short)
    # Shuffle energy+recycle
    team.riders[short].shuffle_deck(False)
    team.riders[short].in_breakaway = False
    store_phase("breakaway_"+str(current_stage.bid_number)+"_end")
    
    return json_update_rider(team.riders[short], team_name)

@app.route("/loser/<string:team_name>/<string:short>/")
def loser(team_name, short):
    team = current_stage.get_team(team_name)
    rider = team.riders[short]
    # Shuffle deck
    rider.shuffle_deck(True)
    rider.in_breakaway = False
    store_phase("breakaway_"+str(current_stage.bid_number)+"_end")
    
    return json_update_rider(rider, team_name)

@app.route("/exhaustion/<string:team_name>/<string:short>/")
def exhaustion(team_name, short):
    global last_exhaustion
    team = current_stage.get_team(team_name)
    rider = team.riders[short]
    # Add exhaustion
    team.add_s(short)
    last_exhaustion.append(team.name+" "+rider.name+"")
    store_phase(str(current_stage.turn_number)+"_end")
    
    # Append exhaustion text
    rider_dict = update_rider(rider, team_name)
    stage_dict = update_stage()
    stage_dict['#stage-output'] += ", ".join(last_exhaustion)
    return jsonify({**rider_dict, **stage_dict })

@app.route("/finished/<string:team_name>/<string:short>/")
def finished(team_name, short):
    team = current_stage.get_team(team_name)
    rider = team.riders[short]
    rider.finished_stage = True
    store_phase(str(current_stage.turn_number)+"_end")
    return json_update_rider(rider, team_name)

@app.route("/play/<string:team_name>/<string:short>/<string:play>")
def play(team_name, short, play):
    team = current_stage.get_team(team_name)
    team.play_s(short+play)
    
    if current_stage.breakaway_started:
        store_phase("breakaway_"+str(current_stage.bid_number)+"_movement")
        set_phase_text(current_stage.output_breakaway_bid_phase())
    else:   
        store_phase(str(current_stage.turn_number)+"_movement")
        set_phase_text(current_stage.output_movement_phase())

    return json_update_rider(team.riders[short], team_name)

@app.route("/in_breakaway/<string:team_name>/<string:short>")
def in_breakaway(team_name, short):
    team = current_stage.get_team(team_name)
    rider = team.riders[short]
    rider.in_breakaway = True
    rider_dict = {}
    for rider in list(team.riders.values()):
        updated_rider = update_rider_min(rider, team_name)
        rider_dict = { **rider_dict, **updated_rider }
    stage_dict = update_stage()
    return jsonify({**rider_dict, **stage_dict })

@app.route("/breakaway")
def breakaway():
    if not stage == None:
        # Enable the rider selection
        if not current_stage.breakaway_started:
            current_stage.breakaway_started = True;
        else:
            current_stage.perform_breakaway_energy_phase()
            store_phase("breakaway_"+str(current_stage.bid_number)+"_energy")
            set_phase_text(current_stage.output_breakaway_energy_phase())
    return redirect(url_for('stage'))

@app.route("/energy")
def energy():
    global last_exhaustion
    last_exhaustion = []
    current_stage.perform_energy_phase()
    store_phase(str(current_stage.turn_number)+"_energy")
    set_phase_text(current_stage.output_energy_phase())
    return redirect(url_for('stage'))
  
@app.route("/determine_turn_order")
def determine_turn_order():
    # Create order
    team_list = list(current_stage.team_dict.keys())
    random.shuffle(team_list)
    text = ""
    while len(team_list)>0:
        text += "{0}\n".format(team_list.pop(0))
    
    set_phase_text(text)
    return jsonify(update_stage())
  
# Helpers
# =======
def json_update_rider(rider, team_name):
    rider_dict = update_rider(rider, team_name)
    stage_dict = update_stage() 
    return jsonify({**rider_dict, **stage_dict })

def set_phase_text(text):
    global phase_text
    phase_text = text
    
def store_phase(filename):
    # Call in energy phases and after every movement
    # /Stage_Name/filename.stage
    directory = os.path.join(stages_dir, current_stage.name)
    if not os.path.isdir(directory):
        os.makedirs(directory)
        os.chown(directory, int(os.getenv('SUDO_UID')), int(os.getenv('SUDO_GID')))
    path = os.path.join(stages_dir, current_stage.name, "{0}.stage".format(filename))
    store_stage(path, current_stage)
  
def get_stage_list():
    return sorted(os.listdir(stages_dir))

def get_files_for_stage(stage_name):
    return sorted(os.listdir(os.path.join(stages_dir,stage_name)), key=lambda x: os.path.getctime(os.path.join(stages_dir,stage_name,x)));    

def create_folder_for_stage(path):
    if os.path.exists(path):
        # If stage exists remove it
        for file in os.listdir(path):
            os.remove(os.path.join(path, file))
    else:
        # Create directory
        os.makedirs(path)
        
def can_display_in_breakaway(team_name):
    # If breakaway has been enabled, and no rider selected
    if not current_stage == None:
        if current_stage.breakaway_started and current_stage.bid_number == 0:
            team = current_stage.get_team(team_name)
            for rider in list(team.riders.values()):
                if rider.in_breakaway:
                    return False
            return True
    return False   

def all_teams_have_nominated_rider():
    if not current_stage == None:
        for team in list(current_stage.team_dict.values()):
            rider_found = False
            for rider in list(team.riders.values()):
                if rider.in_breakaway:
                    rider_found = True
            if not rider_found:
                return False
        return True
    return False

def no_teams_have_nominated_rider():
    if not current_stage == None:
        for team in list(current_stage.team_dict.values()):
            for rider in list(team.riders.values()):
                if rider.in_breakaway:
                    return False
        return True
    return False

def are_unfinished_riders():
    if not current_stage == None:
        for team in list(current_stage.team_dict.values()):
            for rider in list(team.riders.values()):
                if not rider.finished_stage:
                    return True
    return False

def all_riders_have_played_cards(breakaway = False):
    if not current_stage == None:
        for team in list(current_stage.team_dict.values()):
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
    if current_stage.breakaway_started:
        if current_stage.bid_number == 0:
            return all_teams_have_nominated_rider()
        elif current_stage.bid_number == 1:
            return all_riders_have_played_cards(True)
    # If we haven't started the stage or the breakaway
    elif current_stage.turn_number == 0 and current_stage.bid_number == 0:
        return True 
    return False

def can_perform_energy():
    # Check we're not bidding
    if not current_stage == None:
        if are_unfinished_riders():
            if not current_stage.breakaway_started:
                if all_riders_have_played_cards():
                    return True
            elif current_stage.bid_number == 2:
                if all_riders_have_played_cards() and no_teams_have_nominated_rider():
                    return True
    return False

def can_display_winner_loser(rider):
    # If we are in a breakway, second round of bidding has occurred
    if not current_stage == None:
        if current_stage.bid_number == 2 and all_riders_have_played_cards() and rider.in_breakaway:
            return True
    return False

def can_display_rider_options(rider):
    if not current_stage == None:
        if current_stage.turn_number > 0 and all_riders_have_played_cards():
            if not rider.finished_stage:
                return True
    return False

def can_display_turn_order():
    if not current_stage == None:
        if not current_stage.breakaway_started:
            if current_stage.turn_number == 0:
                return True
        elif current_stage.bid_number == 2:
            if all_riders_have_played_cards() and no_teams_have_nominated_rider():
                return True
    return False
    
def can_display_next_stage():
    return not are_unfinished_riders()

# Rendering Functions
# ========= =========
def render_stage():
    teams = []
    for team_key in sorted(list(current_stage.team_dict.keys())):
        teams.append(render_team(current_stage.team_dict[team_key]))
    return render_template("stage.html", name=current_stage.name, teams=teams,
                           actions = render_stage_actions(),
                           phase_text=phase_text)

def render_stage_actions():
    return render_template("stage_actions.html",
                           energy=can_perform_energy(),
                           breakaway=can_perform_breakaway(),
                           turn_order=can_display_turn_order(),
                           next_stage=can_display_next_stage())

def render_team(team):
    riders = []
    for rider_key in sorted(list(team.riders.keys())):
        riders.append(render_rider(team.riders[rider_key], team.name))
    # Determine font colour from team colour relative brightness
    r, g, b = bytearray.fromhex(team.colour.lstrip('#'))
    y = 0.2126 * pow((r/255),2.2) +  0.7151 * pow((g/255),2.2)  +  0.0721 * pow((b/255),2.2)
    text_colour = "black"
    if y < 0.18:
        text_colour = "white"
    return render_template("team.html", name=team.name, riders=riders,
                           colour=team.colour, text_colour=text_colour, player=team.player)

def render_rider(rider, team_name):
    deck = [render_drawn_cards("Hand", rider.drawn_cards, team_name, rider.short_name),
            render_cards("Energy", rider.energy_pile, team_name, rider.short_name),
            render_cards("Recycle", rider.recycle_pile, team_name, rider.short_name),
            render_cards("Discard", rider.discard_pile, team_name, rider.short_name)]

    return render_template("rider.html", deck=deck, team=team_name,
                           title = render_rider_title(rider, team_name),
                           actions = render_actions(rider, team_name))

def render_cards(pile_name, cards, team_name, short_name):
    return render_template("cards.html", name=pile_name, cards=cards, team=team_name,
                           short=short_name)
    
def render_drawn_cards(pile_name, cards, team_name, short_name):
    return render_template("cards_drawn.html", name=pile_name, cards=cards, team=team_name,
                           short=short_name)

def render_rider_title(rider, team_name):
    message = rider.message
    if rider.in_breakaway:
        message = "In Breakaway!"
    return render_template("rider_title.html", name=rider.name, short=rider.short_name,
                           team=team_name, message=message)

def render_actions(rider, team_name):
    return render_template("actions.html", team=team_name, short=rider.short_name,
                           winlose=can_display_winner_loser(rider),
                           breakaway=can_display_in_breakaway(team_name),
                           options=can_display_rider_options(rider))

# Update Functions
# ====== =========
def update_stage():
    data = {
        '#stage-actions'           : render_stage_actions(),
        '#stage-output'            : phase_text
        }
    return data

def update_all_rider_actions():
    data = {}
    for team in list(current_stage.team_dict.values()):
        for rider in list(team.riders.values()):
            prefix = '#'+team.name + '-' + rider.short_name + '-'
            data = {**data,
                    prefix+"actions" : render_actions(rider, team.name),}
    return data

def update_rider_min(rider, team_name):
    prefix = '#'+team_name + '-' + rider.short_name + '-'
    data = {
        prefix+"title"             : render_rider_title(rider, team_name),
        **update_all_rider_actions()
        }
    return data

def update_rider(rider, team_name):
    prefix = '#'+team_name + '-' + rider.short_name + '-'
    data = {
        prefix+"title"             : render_rider_title(rider, team_name),
        prefix+"cards-Hand"        : render_drawn_cards("Hand", rider.drawn_cards, team_name, rider.short_name),
        prefix+"cards-Energy"      : render_cards("Energy", rider.energy_pile, team_name, rider.short_name),
        prefix+"cards-Recycle"     : render_cards("Recycle", rider.recycle_pile, team_name, rider.short_name),
        prefix+"cards-Discard"     : render_cards("Discard", rider.discard_pile, team_name, rider.short_name),
        **update_all_rider_actions()
        }
    return data

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
    