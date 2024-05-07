from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from statsbombpy import sb
import math
import json

WorldCupSBId = 43
WorldCupSBSeasonId = 106


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/matches")
def get_matches():
    competitions = sb.competitions()
    competition = competitions[(competitions["competition_id"] == WorldCupSBId) &
                               (competitions["season_id"] == WorldCupSBSeasonId)]
    matches = sb.matches(competition_id=WorldCupSBId,
                         season_id=WorldCupSBSeasonId).to_json(orient="records")
    competition = competition.to_json(orient="records")
    return {"competition": json.loads(competition)[0], "matches": json.loads(matches)}


@app.get("/api/matches/{match_id}")
def get_match(match_id: int):
    matches = sb.matches(competition_id=WorldCupSBId,
                         season_id=WorldCupSBSeasonId)
    match = matches[matches["match_id"] == match_id].to_json(orient="records")
    return json.loads(match)[0]


@app.get("/api/matches/{match_id}/teams")
def get_match_teams(match_id: int):
    events = sb.events(match_id=match_id, split=True,
                       flatten_attrs=False)
    lineups = events["starting_xis"]
    substitutions = events["substitutions"]
    lineups = lineups.to_json(orient="records")
    substitutions = substitutions.to_json(orient="records")

    res = []
    for lineup in json.loads(lineups):
        team = {"id": lineup["team_id"], "name": lineup["team"]}
        team_players = []
        for player in lineup["tactics"]["lineup"]:
            team_players.append(
                {**player["player"], "position": player["position"], "jersey_number": player["jersey_number"], "team_id": lineup["team_id"], "is_starter": True})
        res.append({**team, "players": team_players})

    for substitution in json.loads(substitutions):
        team_id = substitution["team_id"]
        player = substitution["substitution"]["replacement"]
        player["position"] = substitution["position"]
        player["is_starter"] = False

        for team in res:
            if team["id"] == team_id:
                team["players"].append(player)

    return res


@app.get("/api/matches/{match_id}/pass-tendencies")
def get_match_pass_tendencies(match_id: int):
    events = sb.events(match_id=match_id, split=True,
                       flatten_attrs=False)
    passes = events["passes"].to_dict(orient="records")
    # {[player_id]: {"positions": [0, 0][], passes: {[player_id]: 0}}}
    pass_tendencies = {}
    for pass_ in passes:
        player_id = pass_["player_id"]
        location = pass_["location"]

        if player_id not in pass_tendencies:
            pass_tendencies[player_id] = {
                "positions": [], "passes": {}}

        pass_tendencies[player_id]["positions"].append(location)

        if "recipient" in pass_["pass"]:
            recipient_id = pass_["pass"]["recipient"]["id"]
            if recipient_id not in pass_tendencies[player_id]["passes"]:
                pass_tendencies[player_id]["passes"][recipient_id] = 0
            pass_tendencies[player_id]["passes"][recipient_id] += 1

            end_location = pass_["pass"]["end_location"]
            if recipient_id not in pass_tendencies:
                pass_tendencies[recipient_id] = {
                    "positions": [], "passes": {}}
            pass_tendencies[recipient_id]["positions"].append(end_location)

    # Calculate average position
    for player_id, player in pass_tendencies.items():
        positions = player["positions"]
        if len(positions) == 0:
            continue
        avg_position = [sum(x) / len(positions) for x in zip(*positions)]
        player["avg_position"] = avg_position
        # Remove positions key
        del player["positions"]

    return pass_tendencies


def is_progressive_pass(pass_):
    # A pass is considered progressive if the distance between the starting point and the next touch is:
    goal_location = [120, 40]
    start_location = pass_["location"]
    end_location = pass_["pass_end_location"]

    if start_location[0] >= end_location[0]:
        return False

    start_distance_to_goal = math.sqrt(
        (goal_location[0] - start_location[0])**2 + (goal_location[1] - start_location[1])**2)
    end_distance_to_goal = math.sqrt(
        (goal_location[0] - end_location[0])**2 + (goal_location[1] - end_location[1])**2)

    # at least 30 meters closer to the opponent's goal if the starting and finishing points are within a team's own half
    if start_location[0] < 60 and end_location[0] < 60:
        if abs(start_distance_to_goal - end_distance_to_goal) > 30:
            return True
    # at least 15 meters closer to the opponent's goal if the starting and finishing points are in different halves
    elif start_location[0] < 60 and end_location[0] >= 60:
        if abs(start_distance_to_goal - end_distance_to_goal) > 15:
            return True
    # at least 10 meters closer to the opponent's goal if the starting and finishing points are in the opponent's half
    elif start_location[0] >= 60 and end_location[0] >= 60:
        if abs(start_distance_to_goal - end_distance_to_goal) > 10:
            return True

    return False


@app.get("/api/matches/{match_id}/summary")
def get_match_summary(match_id: int):
    result = {}
    events = sb.events(match_id=match_id, split=True,
                       flatten_attrs=True)
    passes = events["passes"].to_dict(orient="records")
    ball_receipts = events["ball_receipts"].to_dict(orient="records")
    shots = events["shots"].to_dict(orient="records")
    blocks = events["blocks"].to_dict(orient="records")
    interceptions = events["interceptions"].to_dict(orient="records")
    ball_recoveries = events["ball_recoverys"].to_dict(orient="records")
    clearances = events["clearances"].to_dict(orient="records")
    fouls_committed = events["foul_committeds"].to_dict(orient="records")

    for pass_ in passes:
        team_id = pass_["team_id"]
        if team_id not in result:
            result[team_id] = {
                "passes": 0,
                "passes_completed": 0,
                "Touches in Att 3rd": 0,
                "Shots": 0,
                "Shots on Target": 0,
                "Poss": 0,
                "Passing Accuracy": 0,
                "Forward Passing": 0,
                "Def. Actions in Att 3d": 0,
                "Corners": 0,
                "Fouls Committed": 0
            }

        result[team_id]["passes"] += 1

        if pass_["pass_type"] == "Corner":
            result[team_id]["Corners"] += 1

        if not isinstance(pass_["pass_outcome"], str):
            result[team_id]["passes_completed"] += 1
            if is_progressive_pass(pass_):
                result[team_id]["Forward Passing"] += 1

        if pass_["location"][0] >= 80:
            result[team_id]["Touches in Att 3rd"] += 1

    for receipt in ball_receipts:
        team_id = receipt["team_id"]
        if receipt["location"][0] >= 80 and receipt["ball_receipt_outcome"] != "Incomplete":
            result[team_id]["Touches in Att 3rd"] += 1

    for shot in shots:
        team_id = shot["team_id"]
        result[team_id]["Shots"] += 1

        end_location = shot["shot_end_location"]
        if len(end_location) == 3:
            x, y, z = end_location
            if y >= 36 and y <= 44 and z >= 0 and z <= 2.67:
                result[team_id]["Shots on Target"] += 1

    for block in blocks:
        team_id = block["team_id"]
        if block["location"][0] >= 80:
            result[team_id]["Def. Actions in Att 3d"] += 1

    for interception in interceptions:
        team_id = interception["team_id"]
        outcome = interception["interception_outcome"]
        if interception["location"][0] >= 80 and outcome == "Won" or outcome == "Success" or outcome == "Success In Play" or outcome == "Success Out":
            result[team_id]["Def. Actions in Att 3d"] += 1

    for ball_recovery in ball_recoveries:
        team_id = ball_recovery["team_id"]
        if ball_recovery["location"][0] >= 80 and ball_recovery["ball_recovery_recovery_failure"] != True:
            result[team_id]["Def. Actions in Att 3d"] += 1

    for clearance in clearances:
        team_id = clearance["team_id"]
        if clearance["location"][0] >= 80:
            result[team_id]["Def. Actions in Att 3d"] += 1

    for foul in fouls_committed:
        team_id = foul["team_id"]
        result[team_id]["Fouls Committed"] += 1

    team_a, team_b = list(result.keys())
    # Calculate passing accuracy
    result[team_a]["Passing Accuracy"] = round(
        result[team_a]["passes_completed"] / result[team_a]["passes"], 2) * 100
    result[team_b]["Passing Accuracy"] = round(
        result[team_b]["passes_completed"] / result[team_b]["passes"], 2) * 100

    # Calculate possession
    total_passes = result[team_a]["passes_completed"] + \
        result[team_b]["passes_completed"]
    result[team_a]["Poss"] = round(
        result[team_a]["passes"] / total_passes * 100, 0)
    result[team_b]["Poss"] = 100 - result[team_a]["Poss"]

    del result[team_a]["passes_completed"]
    del result[team_a]["passes"]
    del result[team_b]["passes_completed"]
    del result[team_b]["passes"]

    return result


@app.get("/api/matches/{match_id}/player-stats/{player_id}")
def get_player_stats_by_id(match_id: int, player_id: int):
    result = {
        "Minutes Played": 0,  # TODO: Maybe
        "Goals": 0,
        "Assists": 0,
        "Shots on Target": 0,
        "Shots off Target": 0,
        "Shots Blocked": 0,
        "Dribble Attempts (succ.)": 0,
        "Touches": 0,
        "Accurate Passes": 0,
        "Key Passes": 0,
        "Crosses (acc.)": 0,
        "Progressive Passes (acc.)": 0,
        "Ground Duels (won)": 0,
        "Aerial Duels (won)": 0,
        "Possessions lost": 0,
        "Fouls": 0,
        "Fouls Won": 0,
        "Clearances": 0,
        "Blocked Shots": 0,
        "Interceptions": 0,
        "Tackles": 0,
        "Dribbled Past": 0,
    }
    events = sb.events(match_id=match_id, split=True, flatten_attrs=True)
    lineups = events["starting_xis"].to_dict(orient="records")

    keeper_events = list(filter(lambda x: x['player_id'] == player_id,
                                events["goal_keepers"].to_dict(orient="records")))
    shots = list(filter(
        lambda x: x['player_id'] == player_id, events["shots"].to_dict(orient="records")))
    passes = list(filter(
        lambda x: x['player_id'] == player_id, events["passes"].to_dict(orient="records")))
    receptions = list(filter(
        lambda x: x['player_id'] == player_id, events["ball_receipts"].to_dict(orient="records")))
    duels = list(filter(
        lambda x: x['player_id'] == player_id, events["duels"].to_dict(orient="records")))
    fouls = list(filter(
        lambda x: x['player_id'] == player_id, events["foul_committeds"].to_dict(orient="records")))
    fouls_won = list(filter(
        lambda x: x['player_id'] == player_id, events["foul_wons"].to_dict(orient="records")))
    clearances = list(filter(
        lambda x: x['player_id'] == player_id, events["clearances"].to_dict(orient="records")))
    interceptions = list(filter(
        lambda x: x['player_id'] == player_id, events["interceptions"].to_dict(orient="records")))
    dribbles = list(filter(
        lambda x: x['player_id'] == player_id, events["dribbles"].to_dict(orient="records")))
    blocks = list(filter(
        lambda x: x['player_id'] == player_id, events["blocks"].to_dict(orient="records")))
    dribbled_pasts = list(filter(
        lambda x: x['player_id'] == player_id, events["dribbled_pasts"].to_dict(orient="records")))

    position = None
    for lineup in lineups:
        for p in lineup["tactics"]["lineup"]:
            if p["player"]["id"] == player_id:
                position = p["position"]["name"]
                break

    if position is None:
        return Exception("Player not found")

    if position == "Goalkeeper":
        result["Saves"] = 0
        result["Punches"] = 0
        result["Keeper Sweeper"] = 0

        for k in keeper_events:
            if k["goalkeeper_type"] == "Punch":
                result["Punches"] += 1
            elif k["goalkeeper_type"] == "Keeper Sweeper":
                result["Keeper Sweeper"] += 1
            elif "Saved" in k["goalkeeper_type"]:
                result["Saves"] += 1

    for shot in shots:
        outcome = shot["shot_outcome"]
        if outcome == "Goal":
            result["Goals"] += 1
        elif outcome == "Off T" or outcome == "Saved Off T" or outcome == "Wayward":
            result["Shots off Target"] += 1
        elif outcome == "Saved" or outcome == "Saved to Post" or outcome == "Post":
            result["Shots on Target"] += 1
        elif outcome == "Blocked":
            result["Shots Blocked"] += 1

    crosses_att = 0
    crosses_acc = 0
    progr_att = 0
    progr_acc = 0
    for pass_ in passes:
        outcome = pass_["pass_outcome"]
        recipient = pass_["pass_recipient"]

        result["Touches"] += 1

        if recipient is None:
            result["Possessions lost"] += 1
        else:
            result["Accurate Passes"] += 1

        if pass_["pass_shot_assist"] == True:
            result["Key Passes"] += 1

        if pass_["pass_goal_assist"] == True:
            result["Assists"] += 1

        if pass_["pass_cross"] == True:
            crosses_att += 1
            if recipient != math.nan: # FIXME
                crosses_acc += 1

        if is_progressive_pass(pass_):
            progr_att += 1
            if recipient != math.nan: # FIXME
                print(recipient)
                progr_acc += 1

    result["Crosses (acc.)"] = f'{crosses_att} ({crosses_acc})'
    result["Progressive Passes (acc.)"] = f'{progr_att} ({progr_acc})'

    for reception in receptions:
        if reception["ball_receipt_outcome"] == "Incomplete":
            result["Possessions lost"] += 1
        else:
            result["Touches"] += 1

    ground_duels = 0
    ground_duels_won = 0
    aerial_duels = 0
    aerial_duels_won = 0
    for clearance in clearances:
        result["Clearances"] += 1
        if clearance["clearance_aerial_won"] == True:
            aerial_duels += 1
            aerial_duels_won += 1

    for duel in duels:
        outcome = duel["duel_outcome"]
        if duel["duel_type"] == "Aerial Lost":
            aerial_duels += 1
        elif duel["duel_type"] == "Tackle":
            ground_duels += 1
            result["Tackles"] += 1

        if outcome == "Won" or outcome == "Success" or outcome == "Success In Play" or outcome == "Success Out":
            ground_duels_won += 1

    result["Ground Duels (won)"] = f'{ground_duels} ({ground_duels_won})'
    result["Aerial Duels (won)"] = f'{aerial_duels} ({aerial_duels_won})'

    result["Fouls"] = len(fouls)
    result["Fouls Won"] = len(fouls_won)
    result["Blocked Shots"] = len(blocks)

    for interception in interceptions:
        outcome = interception["interception_outcome"]
        if outcome == "Won" or outcome == "Success" or outcome == "Success In Play" or outcome == "Success Out":
            result["Interceptions"] += 1

    dribble_att = 0
    dribble_succ = 0
    for dribble in dribbles:
        dribble_att += 1
        if dribble["dribble_outcome"] == "Complete":
            dribble_succ += 1

    result["Dribble Attempts (succ.)"] = f'{dribble_att} ({dribble_succ})'

    result["Dribbled Past"] = len(dribbled_pasts)

    return result


@app.get("/api/matches/{match_id}/shotchart")
def getPlayerShots(match_id: int):
    events = sb.events(match_id=match_id, split=True,
                       flatten_attrs=False)
    shots = events["shots"].to_dict(orient="records")
    return json.loads(json.dumps(shots).replace("NaN", "null"))


@app.get("/api/matches/{match_id}/events")
def get_match_events(match_id: int):
    events = sb.events(match_id=match_id, split=True, flatten_attrs=True)
    res = {}
    keys_to_ignore = ['starting_xis', 'half_starts', 'half_ends',
                      'player_offs', 'player_ons', 'substitutions', 'tactical_shifts']
    for key in events.keys():
        if key not in keys_to_ignore:
            res[key] = events[key].to_dict(orient='records')

    return json.loads(json.dumps(res).replace("NaN", "null"))
