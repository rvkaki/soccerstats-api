from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import math
import requests


data_url = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/competitions")
def get_competitions():
    competitions = requests.get(f"{data_url}/competitions.json").json()
    return competitions


@app.get("/api/competitions/{competition_id}/season/{season_id}/matches")
def get_matches(competition_id: int, season_id: int):
    matches = requests.get(
        f"{data_url}/matches/{competition_id}/{season_id}.json").json()
    competitions = requests.get(f"{data_url}/competitions.json").json()
    competition = list(
        filter(lambda x: x["competition_id"] == competition_id, competitions))[0]
    return {"competition": competition, "matches": matches}


# @app.get("/api/competitions/{competition_id}/season/{season_id}/teams")
# def get_teams(competition_id: int, season_id: int):
#     matches = requests.get(
#         f"{data_url}/matches/{competition_id}/{season_id}.json").json()
#     teams = {}
#     for match in matches:
#         home_team = match["home_team"]
#         away_team = match["away_team"]
#         if home_team["home_team_id"] not in teams:
#             team_id = home_team["home_team_id"]
#             team = {
#                 "id": team_id,
#                 "name": home_team["home_team_name"],
#                 "country": home_team["country"],
#             }
#         if away_team["away_team_id"] not in teams:
#             team_id = away_team["away_team_id"]
#             team = {
#                 "id": team_id,
#                 "name": away_team["away_team_name"],
#                 "country": away_team["country"],
#             }

#         teams[team_id] = team

#     return list(teams.values())


# @app.get("/api/competitions/{competition_id}/season/{season_id}/players")
# def get_players(competition_id: int, season_id: int):
#     matches = requests.get(
#         f"{data_url}/matches/{competition_id}/{season_id}.json").json()
#     players = {}
#     for match in matches:
#         home_team = match["home_team"]
#         away_team = match["away_team"]
#         home_players = get_team_match_players(
#             home_team["home_team_id"], match["match_id"])
#         away_players = get_team_match_players(
#             away_team["away_team_id"], match["match_id"])

#         for player_id, player in home_players.items():
#             if player_id not in players:
#                 players[player_id] = {
#                     **player, "team_id": home_team["home_team_id"]}
#         for player_id, player in away_players.items():
#             if player_id not in players:
#                 players[player_id] = {
#                     **player, "team_id": away_team["away_team_id"]}

#     return list(players.values())


# @app.get("/api/competitions/{competition_id}/season/{season_id}/players/{player_id}")
# def get_player(player_id: int):
#     matches = requests.get(
#         f"{data_url}/matches/{competition_id}/{season_id}.json").json()
#     for match in matches:
#         home_team = match["home_team"]
#         away_team = match["away_team"]
#         home_players = get_team_match_players(
#             home_team["home_team_id"], match["match_id"])
#         away_players = get_team_match_players(
#             away_team["away_team_id"], match["match_id"])

#         if player_id in home_players:
#             return home_players[player_id]
#         if player_id in away_players:
#             return away_players[player_id]

#     return None


# @app.get("/api/players/{player_id}/totals/actions")
# def get_player_totals_actions(player_id: int, team_id: int):
#     matches = requests.get(
#         f"{data_url}/matches/{competition_id}/{season_id}.json").json()
#     team_matches = list(filter(lambda x: x["home_team"]["home_team_id"]
#                         == team_id or x["away_team"]["away_team_id"] == team_id, matches))
#     player_actions = []
#     for match in team_matches:
#         events = list(requests.get(
#             f"{data_url}/events/{match['match_id']}.json").json())
#         for event in events:
#             if "player" in event:
#                 if event["player"]["id"] == player_id:
#                     player_actions.append(event)

#     return player_actions


# def get_team_match_players(team_id, match_id):
#     events = list(requests.get(f"{data_url}/events/{match_id}.json").json())
#     lineups = list(filter(lambda x: x["type"]
#                    ["name"] == "Starting XI", events))
#     substitutions = list(
#         filter(lambda x: x["type"]["name"] == "Substitution", events))

#     team_players = {}
#     for lineup in lineups:
#         if lineup["team"]["id"] == team_id:
#             for player in lineup["tactics"]["lineup"]:
#                 player_id = player["player"]["id"]
#                 team_players[player_id] = {
#                     **player["player"], "position": player["position"], "jersey_number": player["jersey_number"], "team_id": lineup["team"]["id"]}

#     for substitution in substitutions:
#         if substitution["team"]["id"] == team_id:
#             player = substitution["substitution"]["replacement"]
#             player["position"] = substitution["position"]
#             player_id = player["id"]
#             team_players[player_id] = {
#                 **player, "jersey_number": None, "team_id": lineup["team"]["id"]}

#     return team_players


# @app.get("/api/teams/{team_id}")
# def get_team(team_id: int):
#     matches = requests.get(
#         f"{data_url}/matches/{competition_id}/{season_id}.json").json()
#     team_matches = list(filter(lambda x: x["home_team"]["home_team_id"]
#                         == team_id or x["away_team"]["away_team_id"] == team_id, matches))
#     team = {}
#     for match in team_matches:
#         if match["home_team"]["home_team_id"] == team_id:
#             team["id"] = match["home_team"]["home_team_id"]
#             team["name"] = match["home_team"]["home_team_name"]
#             team["country"] = match["home_team"]["country"]
#             match_players = get_team_match_players(team_id, match["match_id"])
#             if "players" not in team:
#                 team["players"] = {}
#             for player_id, player in match_players.items():
#                 if player_id not in team["players"]:
#                     team["players"][player_id] = player
#             break
#         elif match["away_team"]["away_team_id"] == team_id:
#             team["id"] = match["away_team"]["away_team_id"]
#             team["name"] = match["away_team"]["away_team_name"]
#             team["country"] = match["away_team"]["country"]
#             match_players = get_team_match_players(team_id, match["match_id"])
#             if "players" not in team:
#                 team["players"] = {}
#             for player_id, player in match_players.items():
#                 if player_id not in team["players"]:
#                     team["players"][player_id] = player
#             break

#     return team


@app.get("/api/competitions/{competition_id}/season/{season_id}/matches/{match_id}")
def get_match(competition_id: int, season_id: int, match_id: int):
    matches = requests.get(
        f"{data_url}/matches/{competition_id}/{season_id}.json").json()
    match = list(filter(lambda x: x["match_id"] == match_id, matches))[0]
    return match


@app.get("/api/competitions/{competition_id}/season/{season_id}/matches/{match_id}/teams")
def get_match_teams(competition_id: int, season_id: int, match_id: int):
    events = list(requests.get(f"{data_url}/events/{match_id}.json").json())

    lineups = list(filter(lambda x: x["type"]
                   ["name"] == "Starting XI", events))
    substitutions = list(
        filter(lambda x: x["type"]["name"] == "Substitution", events))

    res = []
    for lineup in lineups:
        team = lineup["team"]
        team_players = []
        for player in lineup["tactics"]["lineup"]:
            team_players.append(
                {**player["player"], "position": player["position"], "jersey_number": player["jersey_number"], "team_id": lineup["team"]["id"], "is_starter": True})
        res.append({**team, "players": team_players})

    for substitution in substitutions:
        team_id = substitution["team"]["id"]
        player = substitution["substitution"]["replacement"]
        player["position"] = substitution["position"]
        player["is_starter"] = False

        for team in res:
            if team["id"] == team_id:
                team["players"].append(player)

    return res


# @app.get("/api/teams/{team_id}/totals/pressing-actions")
# def get_team_totals_pressing_actions(team_id: int):
#     matches = requests.get(
#         f"{data_url}/matches/{competition_id}/{season_id}.json").json()
#     team_matches = list(filter(lambda x: x["home_team"]["home_team_id"]
#                         == team_id or x["away_team"]["away_team_id"] == team_id, matches))
#     team_events = []
#     for match in team_matches:
#         match_id = match["match_id"]
#         actions = get_match_pressing_actions(match_id)
#         team_events.extend(actions)

#     return team_events


# @app.get("/api/teams/{team_id}/totals/defensive-actions")
# def get_team_totals_defensive_actions(team_id: int):
#     matches = requests.get(
#         f"{data_url}/matches/{competition_id}/{season_id}.json").json()
#     team_matches = list(filter(lambda x: x["home_team"]["home_team_id"]
#                         == team_id or x["away_team"]["away_team_id"] == team_id, matches))
#     team_events = []
#     for match in team_matches:
#         match_id = match["match_id"]
#         actions = get_match_defensive_actions(match_id)
#         team_events.extend(actions)

#     return team_events


# @app.get("/api/matches/{match_id}/pass-tendencies")
# def get_match_pass_tendencies(match_id: int):
#     events = list(requests.get(f"{data_url}/events/{match_id}.json").json())
#     passes = list(filter(lambda x: x["type"]["name"] == "Pass", events))
#     # {[player_id]: {"positions": [0, 0][], passes: {[player_id]: 0}}}
#     pass_tendencies = {}
#     for pass_ in passes:
#         player_id = pass_["player"]["id"]
#         location = pass_["location"]

#         if player_id not in pass_tendencies:
#             pass_tendencies[player_id] = {
#                 "positions": [], "passes": {}}

#         pass_tendencies[player_id]["positions"].append(location)

#         if "recipient" in pass_["pass"]:
#             recipient_id = pass_["pass"]["recipient"]["id"]
#             if recipient_id not in pass_tendencies[player_id]["passes"]:
#                 pass_tendencies[player_id]["passes"][recipient_id] = 0
#             pass_tendencies[player_id]["passes"][recipient_id] += 1

#             end_location = pass_["pass"]["end_location"]
#             if recipient_id not in pass_tendencies:
#                 pass_tendencies[recipient_id] = {
#                     "positions": [], "passes": {}}
#             pass_tendencies[recipient_id]["positions"].append(end_location)

#     # Calculate average position
#     for player_id, player in pass_tendencies.items():
#         positions = player["positions"]
#         if len(positions) == 0:
#             continue
#         avg_position = [sum(x) / len(positions) for x in zip(*positions)]
#         player["avg_position"] = avg_position
#         # Remove positions key
#         del player["positions"]

#     return pass_tendencies


def is_progressive_pass(pass_):
    # A pass is considered progressive if the distance between the starting point and the next touch is:
    goal_location = [120, 40]
    start_location = pass_["location"]
    end_location = pass_["pass"]["end_location"]

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


def is_progressive_carry(carry_):
    # A carry is progressive if it is greater than five metres and moves the ball at least five metres towards the opposition goal.
    goal_location = [120, 40]
    start_location = carry_["location"]
    end_location = carry_["carry"]["end_location"]

    if start_location[0] >= end_location[0]:
        return False

    start_distance_to_goal = math.sqrt(
        (goal_location[0] - start_location[0])**2 + (goal_location[1] - start_location[1])**2)
    end_distance_to_goal = math.sqrt(
        (goal_location[0] - end_location[0])**2 + (goal_location[1] - end_location[1])**2)
    carry_distance = math.sqrt(
        (end_location[0] - start_location[0])**2 + (end_location[1] - start_location[1])**2)

    if carry_distance > 5 and abs(start_distance_to_goal - end_distance_to_goal) > 5:
        return True

    return False


# @app.get("/api/matches/{match_id}/summary")
# def get_match_summary(match_id: int):
#     result = {}
#     events = list(requests.get(f"{data_url}/events/{match_id}.json").json())
#     passes = list(filter(lambda x: x["type"]["name"] == "Pass", events))
#     ball_receipts = list(
#         filter(lambda x: x["type"]["name"] == "Ball Receipt*", events))
#     shots = list(filter(lambda x: x["type"]["name"] == "Shot", events))
#     blocks = list(filter(lambda x: x["type"]["name"] == "Block", events))
#     interceptions = list(
#         filter(lambda x: x["type"]["name"] == "Interception", events))
#     ball_recoveries = list(
#         filter(lambda x: x["type"]["name"] == "Ball Recovery", events))
#     clearances = list(
#         filter(lambda x: x["type"]["name"] == "Clearance", events))
#     fouls_committed = list(
#         filter(lambda x: x["type"]["name"] == "Foul Committed", events))

#     for pass_ in passes:
#         team_id = pass_["team"]["id"]
#         if team_id not in result:
#             result[team_id] = {
#                 "passes": 0,
#                 "passes_completed": 0,
#                 "Touches in Att 3rd": 0,
#                 "Shots": 0,
#                 "Shots on Target": 0,
#                 "Poss": 0,
#                 "Passing Accuracy": 0,
#                 "Forward Passing": 0,
#                 "Def. Actions in Att 3d": 0,
#                 "Corners": 0,
#                 "Fouls Committed": 0
#             }

#         result[team_id]["passes"] += 1

#         if "type" in pass_["pass"] and pass_["pass"]["type"]["name"] == "Corner":
#             result[team_id]["Corners"] += 1

#         if "recipient" in pass_["pass"]:
#             result[team_id]["passes_completed"] += 1
#             if is_progressive_pass(pass_):
#                 result[team_id]["Forward Passing"] += 1

#         if pass_["location"][0] >= 80:
#             result[team_id]["Touches in Att 3rd"] += 1

#     for receipt in ball_receipts:
#         team_id = receipt["team"]["id"]
#         if receipt["location"][0] >= 80 and "ball_receipt" in receipt and receipt["ball_receipt"]["outcome"]["name"] != "Incomplete":
#             result[team_id]["Touches in Att 3rd"] += 1

#     for shot in shots:
#         team_id = shot["team"]["id"]
#         result[team_id]["Shots"] += 1

#         end_location = shot["shot"]["end_location"]
#         if len(end_location) == 3:
#             x, y, z = end_location
#             if y >= 36 and y <= 44 and z >= 0 and z <= 2.67:
#                 result[team_id]["Shots on Target"] += 1

#     for block in blocks:
#         team_id = block["team"]["id"]
#         if block["location"][0] >= 80:
#             result[team_id]["Def. Actions in Att 3d"] += 1

#     for interception in interceptions:
#         team_id = interception["team"]["id"]
#         outcome = interception["interception"]["outcome"]
#         if interception["location"][0] >= 80 and outcome == "Won" or outcome == "Success" or outcome == "Success In Play" or outcome == "Success Out":
#             result[team_id]["Def. Actions in Att 3d"] += 1

#     for ball_recovery in ball_recoveries:
#         team_id = ball_recovery["team"]["id"]
#         if ball_recovery["location"][0] >= 80 and "ball_recovery" in ball_recovery and "recovery_failure" in ball_recovery["ball_recovery"] and ball_recovery["ball_recovery"]["recovery_failure"] != True:
#             result[team_id]["Def. Actions in Att 3d"] += 1

#     for clearance in clearances:
#         team_id = clearance["team"]["id"]
#         if clearance["location"][0] >= 80:
#             result[team_id]["Def. Actions in Att 3d"] += 1

#     for foul in fouls_committed:
#         team_id = foul["team"]["id"]
#         result[team_id]["Fouls Committed"] += 1

#     team_a, team_b = list(result.keys())
#     # Calculate passing accuracy
#     result[team_a]["Passing Accuracy"] = round(
#         result[team_a]["passes_completed"] / result[team_a]["passes"], 2) * 100
#     result[team_b]["Passing Accuracy"] = round(
#         result[team_b]["passes_completed"] / result[team_b]["passes"], 2) * 100

#     # Calculate possession
#     total_passes = result[team_a]["passes_completed"] + \
#         result[team_b]["passes_completed"]
#     result[team_a]["Poss"] = round(
#         result[team_a]["passes"] / total_passes * 100, 0)
#     result[team_b]["Poss"] = 100 - result[team_a]["Poss"]

#     del result[team_a]["passes_completed"]
#     del result[team_a]["passes"]
#     del result[team_b]["passes_completed"]
#     del result[team_b]["passes"]

#     return result


# @app.get("/api/matches/{match_id}/player-stats/{player_id}")
# def get_player_stats_by_id(match_id: int, player_id: int):
#     result = {
#         "Goals": 0,
#         "Assists": 0,
#         "Shots on Target": 0,
#         "Shots off Target": 0,
#         "Shots Blocked": 0,
#         "Dribble Attempts (succ.)": 0,
#         "Touches": 0,
#         "Accurate Passes": 0,
#         "Key Passes": 0,
#         "Crosses (acc.)": 0,
#         "Progressive Passes (acc.)": 0,
#         "Ground Duels (won)": 0,
#         "Aerial Duels (won)": 0,
#         "Possessions lost": 0,
#         "Fouls": 0,
#         "Fouls Won": 0,
#         "Clearances": 0,
#         "Blocked Shots": 0,
#         "Interceptions": 0,
#         "Tackles": 0,
#         "Dribbled Past": 0,
#     }
#     events = list(requests.get(f"{data_url}/events/{match_id}.json").json())
#     lineups = list(filter(lambda x: x["type"]
#                    ["name"] == "Starting XI", events))

#     keeper_events = list(filter(
#         lambda x: x["type"]["name"] == "Goal Keeper" and x['player']["id"] == player_id, events))
#     shots = list(filter(
#         lambda x: x["type"]["name"] == "Shot" and x['player']["id"] == player_id, events))
#     passes = list(filter(
#         lambda x: x["type"]["name"] == "Pass" and x['player']["id"] == player_id, events))
#     receptions = list(filter(
#         lambda x: x["type"]["name"] == "Ball Receipt*" and x['player']["id"] == player_id, events))
#     duels = list(filter(
#         lambda x: x["type"]["name"] == "Duel" and x['player']["id"] == player_id, events))
#     fouls = list(filter(
#         lambda x: x["type"]["name"] == "Foul Committed" and x['player']["id"] == player_id, events))
#     fouls_won = list(filter(
#         lambda x: x["type"]["name"] == "Foul Won" and x['player']["id"] == player_id, events))
#     clearances = list(filter(
#         lambda x: x["type"]["name"] == "Clearance" and x['player']["id"] == player_id, events))
#     interceptions = list(filter(
#         lambda x: x["type"]["name"] == "Interception" and x['player']["id"] == player_id, events))
#     dribbles = list(filter(
#         lambda x: x["type"]["name"] == "Dribble" and x['player']["id"] == player_id, events))
#     blocks = list(filter(
#         lambda x: x["type"]["name"] == "Block" and x['player']["id"] == player_id, events))
#     dribbled_pasts = list(filter(
#         lambda x: x["type"]["name"] == "Dribbled Past" and x['player']["id"] == player_id, events))

#     position = None
#     for lineup in lineups:
#         for p in lineup["tactics"]["lineup"]:
#             if p["player"]["id"] == player_id:
#                 position = p["position"]["name"]
#                 break

#     if position is None:
#         return Exception("Player not found")

#     if position == "Goalkeeper":
#         result["Saves"] = 0
#         result["Punches"] = 0
#         result["Keeper Sweeper"] = 0

#         for k in keeper_events:
#             if k["goalkeeper"]["type"]["name"] == "Punch":
#                 result["Punches"] += 1
#             elif k["goalkeeper"]["type"]["name"] == "Keeper Sweeper":
#                 result["Keeper Sweeper"] += 1
#             elif "Saved" in k["goalkeeper"]["type"]["name"]:
#                 result["Saves"] += 1

#     for shot in shots:
#         outcome = shot["shot"]["outcome"]["name"]
#         if outcome == "Goal":
#             result["Goals"] += 1
#         elif outcome == "Off T" or outcome == "Saved Off T" or outcome == "Wayward":
#             result["Shots off Target"] += 1
#         elif outcome == "Saved" or outcome == "Saved to Post" or outcome == "Post":
#             result["Shots on Target"] += 1
#         elif outcome == "Blocked":
#             result["Shots Blocked"] += 1

#     crosses_att = 0
#     crosses_acc = 0
#     progr_att = 0
#     progr_acc = 0
#     for pass_ in passes:
#         result["Touches"] += 1

#         if "recipient" not in pass_["pass"]:
#             result["Possessions lost"] += 1
#         else:
#             result["Accurate Passes"] += 1

#         if "shot_assist" in pass_["pass"]:
#             result["Key Passes"] += 1

#         if "goal_assist" in pass_["pass"]:
#             result["Assists"] += 1

#         if "cross" in pass_["pass"]:
#             crosses_att += 1
#             if "recipient" in pass_["pass"]:
#                 crosses_acc += 1

#         if is_progressive_pass(pass_):
#             progr_att += 1
#             if "recipient" in pass_["pass"]:
#                 progr_acc += 1

#     result["Crosses (acc.)"] = f'{crosses_att} ({crosses_acc})'
#     result["Progressive Passes (acc.)"] = f'{progr_att} ({progr_acc})'

#     for reception in receptions:
#         if "ball_receipt" in reception and reception["ball_receipt"]["outcome"]["name"] == "Incomplete":
#             result["Possessions lost"] += 1
#         else:
#             result["Touches"] += 1

#     ground_duels = 0
#     ground_duels_won = 0
#     aerial_duels = 0
#     aerial_duels_won = 0
#     for clearance in clearances:
#         result["Clearances"] += 1
#         if "aerial_won" in clearance["clearance"] and clearance["clearance"]["aerial_won"] == True:
#             aerial_duels += 1
#             aerial_duels_won += 1

#     for duel in duels:
#         if duel["duel"]["type"]["name"] == "Aerial Lost":
#             aerial_duels += 1
#         elif duel["duel"]["type"]["name"] == "Tackle":
#             ground_duels += 1
#             result["Tackles"] += 1

#         if "outcome" in duel["duel"]:
#             outcome = duel["duel"]["outcome"]["name"]
#             if outcome == "Won" or outcome == "Success" or outcome == "Success In Play" or outcome == "Success Out":
#                 ground_duels_won += 1

#     result["Ground Duels (won)"] = f'{ground_duels} ({ground_duels_won})'
#     result["Aerial Duels (won)"] = f'{aerial_duels} ({aerial_duels_won})'

#     result["Fouls"] = len(fouls)
#     result["Fouls Won"] = len(fouls_won)
#     result["Blocked Shots"] = len(blocks)

#     for interception in interceptions:
#         outcome = interception["interception"]["outcome"]["name"]
#         if outcome == "Won" or outcome == "Success" or outcome == "Success In Play" or outcome == "Success Out":
#             result["Interceptions"] += 1

#     dribble_att = 0
#     dribble_succ = 0
#     for dribble in dribbles:
#         dribble_att += 1
#         if dribble["dribble"]["outcome"]["name"] == "Complete":
#             dribble_succ += 1

#     result["Dribble Attempts (succ.)"] = f'{dribble_att} ({dribble_succ})'

#     result["Dribbled Past"] = len(dribbled_pasts)

#     return result


# @app.get("/api/matches/{match_id}/shotchart")
# def getPlayerShots(match_id: int):
#     events = list(requests.get(f"{data_url}/events/{match_id}.json").json())
#     shots = list(filter(lambda x: x["type"]["name"] == "Shot", events))
#     return shots


# @app.get("/api/matches/{match_id}/events")
# def get_match_events(match_id: int):
#     events = list(requests.get(f"{data_url}/events/{match_id}.json").json())
#     keys_to_ignore = ['Starting XI', 'Half Start', 'Half End',
#                       'Player Off', 'Player On', 'Substitution', 'Tactical Shift', 'Referee Ball-Drop', 'Injury Stoppage']
#     # Group events by type
#     res = {}
#     for event in events:
#         event_type = event["type"]["name"]
#         if event_type in keys_to_ignore:
#             continue
#         if event_type not in res:
#             res[event_type] = []
#         res[event_type].append(event)

#     return res


# @app.get("/api/matches/{match_id}/player-actions/{player_id}")
# def get_player_actions(match_id: int, player_id: int):
#     action_type = "Pass"
#     events = list(requests.get(f"{data_url}/events/{match_id}.json").json())
#     events360 = list(requests.get(
#         f"{data_url}/three-sixty/{match_id}.json").json())
#     player_events = list(filter(
#         lambda x:  x["type"]["name"] == action_type and x["player"]["id"] == player_id, events))
#     res = []
#     for event in player_events:
#         if "related_events" in event:
#             related_events = list(
#                 filter(lambda x: x["id"] in event["related_events"], events))
#             for related_event in related_events:
#                 re_360 = list(
#                     filter(lambda x: x["event_uuid"] == related_event["id"], events360))
#                 if len(re_360) > 0:
#                     related_event["event360"] = re_360[0]
#                     related_event["type"] = related_event["type"]["name"]
#         else:
#             related_events = []

#         event360 = list(
#             filter(lambda x: x["event_uuid"] == event["id"], events360))
#         if len(event360) > 0:
#             event360 = event360[0]
#             event_type = event["type"]["name"]
#             res.append(
#                 {**event, "type": event_type, "related_events": related_events, "event360": event360})

#     return res


# @app.get("/api/matches/{match_id}/progressive-passes")
# def get_match_progressive_passes(match_id: int):
#     events = list(requests.get(f"{data_url}/events/{match_id}.json").json())
#     passes = list(filter(lambda x: x["type"]["name"] == "Pass", events))

#     progressive_passes = []
#     for pass_ in passes:
#         if "recipient" in pass_["pass"]:
#             if is_progressive_pass(pass_):
#                 progressive_passes.append(pass_)

#     return progressive_passes


# @app.get("/api/matches/{match_id}/passes-into-box")
# def get_match_progressive_passes(match_id: int):
#     events = list(requests.get(f"{data_url}/events/{match_id}.json").json())
#     passes = list(filter(lambda x: x["type"]["name"] == "Pass", events))

#     passes_into_box = []
#     for pass_ in passes:
#         if "recipient" in pass_["pass"]:
#             end_location = pass_["pass"]["end_location"]
#             if end_location[0] >= 102 and end_location[1] >= 18 and end_location[1] <= 62:
#                 passes_into_box.append(pass_)

#     return passes_into_box


# @app.get("/api/matches/{match_id}/chance-creating-passes")
# def get_match_progressive_passes(match_id: int):
#     events = list(requests.get(f"{data_url}/events/{match_id}.json").json())
#     passes = list(filter(lambda x: x["type"]["name"] == "Pass", events))

#     chanceCreatingPasses = []
#     for pass_ in passes:
#         if "recipient" in pass_["pass"]:
#             if "shot_assist" in pass_["pass"] or "goal_assist" in pass_["pass"]:
#                 chanceCreatingPasses.append(pass_)

#     return chanceCreatingPasses


# @app.get("/api/matches/{match_id}/defensive-actions")
# def get_match_defensive_actions(match_id: int):
#     events = list(requests.get(f"{data_url}/events/{match_id}.json").json())
#     actions = []

#     for event in events:
#         if event["type"]["name"] == "Interception":
#             if "outcome" in event["interception"]:
#                 outcome = event["interception"]["outcome"]["name"]
#                 if outcome == "Won" or outcome == "Success" or outcome == "Success In Play" or outcome == "Success Out":
#                     actions.append(event)
#         elif event["type"]["name"] == "Duel":
#             if "outcome" in event["duel"]:
#                 outcome = event["duel"]["outcome"]["name"]
#                 if outcome == "Won" or outcome == "Success" or outcome == "Success In Play" or outcome == "Success Out":
#                     actions.append(event)
#         elif event["type"]["name"] == "Ball Recovery":
#             if "ball_recovery" in event and "recovery_failure" not in event["ball_recovery"]:
#                 actions.append(event)
#         elif event["type"]["name"] == "Clearance":
#             actions.append(event)
#         elif event["type"]["name"] == "Block":
#             if "block" in event and "offensive" not in event["block"]:
#                 actions.append(event)
#         elif event["type"]["name"] == "Foul Committed":
#             if "foul_committed_offensive" not in event:
#                 actions.append(event)

#     return actions


# @app.get("/api/matches/{match_id}/pressing-actions")
# def get_match_pressing_actions(match_id: int):
#     events = list(requests.get(f"{data_url}/events/{match_id}.json").json())
#     actions = []

#     for event in events:
#         if event["type"]["name"] == "Pressure":
#             actions.append(event)

#     return actions


@app.get("/api/competitions/{competition_id}/season/{season_id}/matches/{match_id}/compare")
def get_match_compare_stats(competition_id: int, season_id: int, match_id: int, ids: str, stat: str):
    ids = list(map(int, ids.split(",")))
    events = list(requests.get(f"{data_url}/events/{match_id}.json").json())

    res = {}
    if stat == "passes.progressive":
        for event in events:
            if event["type"]["name"] == "Pass":
                player_id = event["player"]["id"]
                team_id = event["team"]["id"]
                if player_id in ids:
                    if player_id not in res:
                        res[player_id] = []
                    if is_progressive_pass(event):
                        res[player_id].append(event)
                elif team_id in ids:
                    if team_id not in res:
                        res[team_id] = []
                    if is_progressive_pass(event):
                        res[team_id].append(event)
    elif stat == "passes.into_box":
        for event in events:
            if event["type"]["name"] == "Pass":
                player_id = event["player"]["id"]
                team_id = event["team"]["id"]
                end_location = event["pass"]["end_location"]
                if player_id in ids:
                    if player_id not in res:
                        res[player_id] = []
                    if end_location[0] >= 102 and end_location[1] >= 18 and end_location[1] <= 62:
                        res[player_id].append(event)
                elif team_id in ids:
                    if team_id not in res:
                        res[team_id] = []
                    if end_location[0] >= 102 and end_location[1] >= 18 and end_location[1] <= 62:
                        res[team_id].append(event)
    elif stat == "passes.chance_creation":
        for event in events:
            if event["type"]["name"] == "Pass":
                player_id = event["player"]["id"]
                team_id = event["team"]["id"]
                if player_id in ids:
                    if player_id not in res:
                        res[player_id] = []
                    if "shot_assist" in event["pass"] or "goal_assist" in event["pass"]:
                        res[player_id].append(event)
                elif team_id in ids:
                    if team_id not in res:
                        res[team_id] = []
                    if "shot_assist" in event["pass"] or "goal_assist" in event["pass"]:
                        res[team_id].append(event)
    elif stat == "passes.total":
        for event in events:
            if event["type"]["name"] == "Pass":
                player_id = event["player"]["id"]
                team_id = event["team"]["id"]
                if player_id in ids:
                    if player_id not in res:
                        res[player_id] = []
                    res[player_id].append(event)
                elif team_id in ids:
                    if team_id not in res:
                        res[team_id] = []
                    res[team_id].append(event)
    elif stat == "shots.total":
        for event in events:
            if event["type"]["name"] == "Shot":
                player_id = event["player"]["id"]
                team_id = event["team"]["id"]
                if player_id in ids:
                    if player_id not in res:
                        res[player_id] = []
                    res[player_id].append(event)
                elif team_id in ids:
                    if team_id not in res:
                        res[team_id] = []
                    res[team_id].append(event)
    elif stat == "shots.on_target":
        for event in events:
            if event["type"]["name"] == "Shot":
                player_id = event["player"]["id"]
                team_id = event["team"]["id"]
                end_location = event["shot"]["end_location"]
                if player_id in ids:
                    if player_id not in res:
                        res[player_id] = []
                    if len(end_location) == 3:
                        x, y, z = end_location
                        if y >= 36 and y <= 44 and z >= 0 and z <= 2.67:
                            res[player_id].append(event)
                    else:
                        x, y = end_location
                        if y >= 36 and y <= 44:
                            res[player_id].append(event)
                elif team_id in ids:
                    if team_id not in res:
                        res[team_id] = []
                    if len(end_location) == 3:
                        x, y, z = end_location
                        if y >= 36 and y <= 44 and z >= 0 and z <= 2.67:
                            res[team_id].append(event)
                    else:
                        x, y = end_location
                        if y >= 36 and y <= 44:
                            res[team_id].append(event)
    elif stat == "defensive_actions.total":
        for event in events:
            if event["type"]["name"] == "Interception" or event["type"]["name"] == "Ball Recovery" or event["type"]["name"] == "Clearance" or event["type"]["name"] == "Block" or event["type"]["name"] == "Duel":
                player_id = event["player"]["id"]
                team_id = event["team"]["id"]
                if player_id in ids:
                    if player_id not in res:
                        res[player_id] = []
                    res[player_id].append(event)
                elif team_id in ids:
                    if team_id not in res:
                        res[team_id] = []
                    res[team_id].append(event)
    elif stat == "defensive_actions.interception":
        for event in events:
            if event["type"]["name"] == "Interception":
                player_id = event["player"]["id"]
                team_id = event["team"]["id"]
                if player_id in ids:
                    if player_id not in res:
                        res[player_id] = []
                    res[player_id].append(event)
                elif team_id in ids:
                    if team_id not in res:
                        res[team_id] = []
                    res[team_id].append(event)
    elif stat == "defensive_actions.clearance":
        for event in events:
            if event["type"]["name"] == "Clearance":
                player_id = event["player"]["id"]
                team_id = event["team"]["id"]
                if player_id in ids:
                    if player_id not in res:
                        res[player_id] = []
                    res[player_id].append(event)
                elif team_id in ids:
                    if team_id not in res:
                        res[team_id] = []
                    res[team_id].append(event)
    elif stat == "defensive_actions.block":
        for event in events:
            if event["type"]["name"] == "Block":
                player_id = event["player"]["id"]
                team_id = event["team"]["id"]
                if player_id in ids:
                    if player_id not in res:
                        res[player_id] = []
                    res[player_id].append(event)
                elif team_id in ids:
                    if team_id not in res:
                        res[team_id] = []
                    res[team_id].append(event)
    elif stat == "defensive_actions.ball_recovery":
        for event in events:
            if event["type"]["name"] == "Ball Recovery":
                player_id = event["player"]["id"]
                team_id = event["team"]["id"]
                if player_id in ids:
                    if player_id not in res:
                        res[player_id] = []
                    res[player_id].append(event)
                elif team_id in ids:
                    if team_id not in res:
                        res[team_id] = []
                    res[team_id].append(event)
    elif stat == "defensive_actions.duel":
        for event in events:
            if event["type"]["name"] == "Duel":
                player_id = event["player"]["id"]
                team_id = event["team"]["id"]
                if player_id in ids:
                    if player_id not in res:
                        res[player_id] = []
                    res[player_id].append(event)
                elif team_id in ids:
                    if team_id not in res:
                        res[team_id] = []
                    res[team_id].append(event)
    elif stat == "carries.total":
        for event in events:
            if event["type"]["name"] == "Carry":
                player_id = event["player"]["id"]
                team_id = event["team"]["id"]
                if player_id in ids:
                    if player_id not in res:
                        res[player_id] = []
                    res[player_id].append(event)
                elif team_id in ids:
                    if team_id not in res:
                        res[team_id] = []
                    res[team_id].append(event)
    elif stat == "carries.progressive":
        for event in events:
            if event["type"]["name"] == "Carry":
                player_id = event["player"]["id"]
                team_id = event["team"]["id"]
                if player_id in ids:
                    if player_id not in res:
                        res[player_id] = []
                    if is_progressive_carry(event):
                        res[player_id].append(event)
                elif team_id in ids:
                    if team_id not in res:
                        res[team_id] = []
                    if is_progressive_carry(event):
                        res[team_id].append(event)
    elif stat == "pressure.total":
        for event in events:
            if event["type"]["name"] == "Pressure":
                player_id = event["player"]["id"]
                team_id = event["team"]["id"]
                if player_id in ids:
                    if player_id not in res:
                        res[player_id] = []
                    res[player_id].append(event)
                elif team_id in ids:
                    if team_id not in res:
                        res[team_id] = []
                    res[team_id].append(event)
    elif stat == "dribbles.total":
        for event in events:
            if event["type"]["name"] == "Dribble":
                player_id = event["player"]["id"]
                team_id = event["team"]["id"]
                if player_id in ids:
                    if player_id not in res:
                        res[player_id] = []
                    res[player_id].append(event)
                elif team_id in ids:
                    if team_id not in res:
                        res[team_id] = []
                    res[team_id].append(event)
    elif stat == "heatmaps":
        for event in events:
            #  "Substitution," "Half Start," "Half End," "Injury Stoppage," or "Tactical Shift"
            if event["type"]["name"] in ["Substitution", "Half Start", "Half End", "Injury Stoppage", "Tactical Shift", "Starting XI", "Referee Ball-Drop"]:
                continue
            player_id = event["player"]["id"]
            team_id = event["team"]["id"]
            if player_id in ids:
                if player_id not in res:
                    res[player_id] = []
                res[player_id].append(event)
            elif team_id in ids:
                if team_id not in res:
                    res[team_id] = []
                res[team_id].append(event)
    else:
        return Exception("Invalid stat")

    for id in ids:
        if id not in res:
            res[id] = []

    return res
