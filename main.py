from fastapi import FastAPI
from statsbombpy import sb
import soccerdata as sd
import math
import json
from constants import WorldCupSBId, WorldCupSBSeasonId, WorldCupFBRefId, WorldCupFBRefSeasonId

app = FastAPI()


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


def getPlayerShots(events, player_id):
    shots = events["shots"].to_dict(orient="records")
    player_shots = []
    for shot in shots:
        if shot["player_id"] == player_id:
            player_shots.append(shot)
    return player_shots


def getPlayerProgressivePasses(events, player_id):
    passes = events["passes"].to_dict(orient="records")
    player_passes = []
    for pass_ in passes:
        if pass_["player_id"] == player_id:
            # A pass is considered progressive if the distance between the starting point and the next touch is:
            goal_location = [120, 40]
            start_location = pass_["location"]
            end_location = pass_["pass"]["end_location"]

            if start_location[0] >= end_location[0]:
                continue

            start_distance_to_goal = math.sqrt(
                (goal_location[0] - start_location[0])**2 + (goal_location[1] - start_location[1])**2)
            end_distance_to_goal = math.sqrt(
                (goal_location[0] - end_location[0])**2 + (goal_location[1] - end_location[1])**2)

            # at least 30 meters closer to the opponent's goal if the starting and finishing points are within a team's own half
            if start_location[0] < 60 and end_location[0] < 60:
                if abs(start_distance_to_goal - end_distance_to_goal) > 30:
                    player_passes.append(pass_)
            # at least 15 meters closer to the opponent's goal if the starting and finishing points are in different halves
            elif start_location[0] < 60 and end_location[0] >= 60:
                if abs(start_distance_to_goal - end_distance_to_goal) > 15:
                    player_passes.append(pass_)
            # at least 10 meters closer to the opponent's goal if the starting and finishing points are in the opponent's half
            elif start_location[0] >= 60 and end_location[0] >= 60:
                if abs(start_distance_to_goal - end_distance_to_goal) > 10:
                    player_passes.append(pass_)
    return player_passes


def getPlayerProgressiveCarries(events, player_id):
    carries = events["carrys"].to_dict(orient="records")
    player_carries = []

    for carry in carries:
        if carry["player_id"] == player_id:
            # A run is considered progressive if the distance before the starting point and the last touch of the player is:
            goal_location = [120, 40]
            start_location = carry["location"]
            end_location = carry["carry"]["end_location"]

            if start_location[0] >= end_location[0]:
                continue

            start_distance_to_goal = math.sqrt(
                (goal_location[0] - start_location[0])**2 + (goal_location[1] - start_location[1])**2)
            end_distance_to_goal = math.sqrt(
                (goal_location[0] - end_location[0])**2 + (goal_location[1] - end_location[1])**2)

            # at least 30 meters closer to opponent goal if starting and finishing points are in own half
            if start_location[0] < 60 and end_location[0] < 60:
                if abs(start_distance_to_goal - end_distance_to_goal) > 30:
                    player_carries.append(carry)
            # at least 15 meters closer to opponent goal if starting and finishing points are in different field halves
            elif start_location[0] < 60 and end_location[0] >= 60:
                if abs(start_distance_to_goal - end_distance_to_goal) > 15:
                    player_carries.append(carry)
            # at least 10 meters closer to opponent goal if starting and finishing points are in opponent half
            elif start_location[0] >= 60 and end_location[0] >= 60:
                if abs(start_distance_to_goal - end_distance_to_goal) > 10:
                    player_carries.append(carry)
    return player_carries


def getPlayerDribbles(events, player_id):
    dribbles = events["dribbles"].to_dict(orient="records")
    player_dribbles = []
    for shot in dribbles:
        if shot["player_id"] == player_id:
            player_dribbles.append(shot)
    return player_dribbles


def getPlayerBallsLost(events, player_id):
    passes = events["passes"].to_dict(orient="records")
    duels = events["duels"].to_dict(orient="records")
    dribbles = events["dribbles"].to_dict(orient="records")
    fouls_committed = events["foul_committeds"].to_dict(orient="records")
    miscontrols = events["miscontrols"].to_dict(orient="records")
    dispossessed = events["dispossesseds"].to_dict(orient="records")

    balls_lost = []
    for pass_ in passes:
        if pass_["player_id"] == player_id and "outcome" in pass_["pass"]:
            pass_outcome = pass_["pass"]["outcome"]["name"]
            if (pass_outcome == "Incomplete" or pass_outcome == "Out" or pass_outcome == "Pass Offside"):
                balls_lost.append(pass_)
    for duel in duels:
        if duel["player_id"] == player_id and "outcome" in duel["duel"]:
            duel_outcome = duel["duel"]["outcome"]["name"]
            if (duel_outcome == "Lost In Play" or duel_outcome == "Lost Out"):
                balls_lost.append(duel)
    for dribble in dribbles:
        if dribble["player_id"] == player_id and "outcome" in dribble["dribble"]:
            dribble_outcome = dribble["dribble"]["outcome"]["name"]
            if dribble_outcome == "Incomplete":
                balls_lost.append(dribble)
    for foul in fouls_committed:
        if foul["player_id"] == player_id:
            balls_lost.append(foul)
    for miscontrol in miscontrols:
        if miscontrol["player_id"] == player_id:
            balls_lost.append(miscontrol)
    for dispossess in dispossessed:
        if dispossess["player_id"] == player_id:
            balls_lost.append(dispossess)

    return balls_lost


def getPlayerDefensiveActions(events, player_id):
    blocks = events["blocks"].to_dict(orient="records")
    interceptions = events["interceptions"].to_dict(orient="records")
    ball_recoveries = events["ball_recoverys"].to_dict(orient="records")
    duels = events["duels"].to_dict(orient="records")
    clearances = events["clearances"].to_dict(orient="records")

    defensive_actions = []
    for block in blocks:
        if block["player_id"] == player_id:
            defensive_actions.append(block)
    for interception in interceptions:
        if interception["player_id"] == player_id and "outcome" in interception["interception"]:
            interception_outcome = interception["interception"]["outcome"]["name"]
            if interception_outcome == "Won" or interception_outcome == "Success" or interception_outcome == "Success In Play" or interception_outcome == "Success Out":
                defensive_actions.append(interception)
    for ball_recovery in ball_recoveries:
        if ball_recovery["player_id"] == player_id:
            if isinstance(ball_recovery["ball_recovery"], float) and math.isnan(ball_recovery["ball_recovery"]):
                defensive_actions.append(ball_recovery)
            else:
                if "recovery_failure" not in ball_recovery["ball_recovery"]:
                    defensive_actions.append(ball_recovery)
    for duel in duels:
        if duel["player_id"] == player_id and "outcome" in duel["duel"]:
            duel_outcome = duel["duel"]["outcome"]["name"]
            if duel_outcome == "Won" or duel_outcome == "Success" or duel_outcome == "Success In Play" or duel_outcome == "Success Out":
                defensive_actions.append(duel)
    for clearance in clearances:
        if clearance["player_id"] == player_id:
            defensive_actions.append(clearance)

    return defensive_actions


@app.get("/api/matches/{match_id}/player-stats/{player_id}")
def get_match_player_stats(match_id: int, player_id: int):
    events = sb.events(match_id=match_id, split=True,
                       flatten_attrs=False)
    print("Events keys", events.keys())

    player_shots = getPlayerShots(events, player_id)
    player_passes = getPlayerProgressivePasses(events, player_id)
    player_carries = getPlayerProgressiveCarries(events, player_id)
    player_dribbles = getPlayerDribbles(events, player_id)
    balls_lost = getPlayerBallsLost(events, player_id)

    res = {}

    res["shots"] = player_shots
    res["passes"] = player_passes
    res["carries"] = player_carries
    res["dribbles"] = player_dribbles
    res["balls_lost"] = balls_lost
    res["defensive_actions"] = getPlayerDefensiveActions(events, player_id)

    return json.loads(json.dumps(res).replace("NaN", "null"))


@app.get("/api/matches/{match_id}")
def get_match_by_id(match_id: int):
    res = {}
    # all_events = list(sb.events(match_id=22912, fmt='raw').values())
    events = sb.events(match_id=match_id, split=True,
                       flatten_attrs=False)
    # print events keys

    passes = events["passes"]
    shots = events["shots"]
    dribbles = events["dribbles"]
    lineups = events["starting_xis"]
    substitutions = events["substitutions"]
    res["lineups"] = lineups.to_json(orient="records")
    res["substitutions"] = substitutions.to_json(orient="records")
    res["passes"] = passes.to_json(orient="records")
    res["shots"] = shots.to_json(orient="records")
    res["dribbles"] = dribbles.to_json(orient="records")

    return res


@app.get("/api/matches/{match_id}/goals")
def get_match_goals(match_id: int):
    events = sb.events(match_id=match_id, split=True,
                       flatten_attrs=False)
    shots = events["shots"]

    goals = []
    for shot in shots.to_dict(orient="records"):
        if shot["shot"]['outcome']["name"] == "Goal":
            goals.append(shot)

    for goal in goals:
        goal["events"] = get_goal_play(match_id, goal["id"])

    return json.dumps(goals).replace("NaN", "null")


def get_goal_play(match_id: int, event_id: int):
    all_events = list(sb.events(match_id=match_id, fmt='raw').values())

    goal_event = None
    for index, event in enumerate(all_events):
        if event["id"] == event_id:
            goal_event = event
            break

    events = []
    possession = goal_event['possession']
    while all_events[index]['possession'] == possession:
        events.append(all_events[index])
        index -= 1

    events = list(reversed(events))
    return events


# FBREF API

# @app.get("/api/teams/{team_id}")
# def get_team(team_id: int):
#     fbref = sd.FBref(leagues=WorldCupFBRefId, seasons=WorldCupFBRefSeasonId)
#     stats = fbref.read_player_match_stats()
#     for key, row in stats.iterrows():
#         print(key)
#         # ('PRT-PrimeiraLiga', '2324', '2023-08-11 Braga-Famalicão', 'Braga', 'Abel Ruiz')
#         stat = row.to_dict()
#         print(stat)
#         for key, value in row.items():
#             keys = list(key)
#             print(keys, value)  # ['min', ''] 90 / ['Performance', 'Gls'] 0
#         exit()

# Find in a pandas dataframe the row where match_report includes {match_id}
# Assume matches is a pandas dataframe with a column match_report
# match = matches[matches["match_report"].str.contains(match_id)]
