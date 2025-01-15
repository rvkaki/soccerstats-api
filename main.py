from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import math
import requests
import json

EURO_24_COMPETITION_ID = 55
EURO_24_SEASON_ID = 282

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


@app.get("/api/competitions/{competition_id}/season/{season_id}/matches/{match_id}")
def get_match(competition_id: int, season_id: int, match_id: int):
    matches = requests.get(
        f"{data_url}/matches/{competition_id}/{season_id}.json").json()
    match = list(filter(lambda x: x["match_id"] == match_id, matches))[0]
    return match


@app.get("/api/competitions/{competition_id}/season/{season_id}/matches/{match_id}/teams")
def get_match_teams(competition_id: int, season_id: int, match_id: int):
    players_info = {}
    if (competition_id == EURO_24_COMPETITION_ID and season_id == EURO_24_SEASON_ID):
        players_info = json.load(open("euro24_players.json"))

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
            player_id = player["player"]["id"]
            player_info = players_info[str(player_id)] if str(player_id) in players_info else {
                "jersey_number": None, "img": None, "nickname": None}
            team_players.append(
                {**player["player"], "position": player["position"], "team_id": lineup["team"]["id"], "is_starter": True, "jersey_number": player["jersey_number"] if player["jersey_number"] else player_info["jersey_number"], "img": player_info["img"], "nickname": player_info["nickname"]})
        res.append({**team, "players": team_players})

    for substitution in substitutions:
        team_id = substitution["team"]["id"]
        player = substitution["substitution"]["replacement"]
        player["position"] = substitution["position"]
        player["is_starter"] = False
        player_id = player["id"]
        player_info = players_info[str(player_id)] if str(player_id) in players_info else {
            "jersey_number": None, "img": None, "nickname": None}

        for team in res:
            if team["id"] == team_id:
                team["players"].append(
                    {**player, "team_id": team_id, "jersey_number": player_info["jersey_number"], "img": player_info["img"], "nickname": player_info["nickname"]})

    return res


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


@app.get("/api/competitions/{competition_id}/season/{season_id}/matches/{match_id}/compare")
def get_match_compare_stats(competition_id: int, season_id: int, match_id: int, ids: str, stat: str):
    ids = list(map(int, ids.split(",")))
    events = list(requests.get(f"{data_url}/events/{match_id}.json").json())

    res = {}
    if stat == "passes.progressive_made":
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
    elif stat == "passes.progressive_received":
        for event in events:
            if event["type"]["name"] == "Pass":
                player_id = event["player"]["id"]
                team_id = event["team"]["id"]
                if player_id in ids:
                    if player_id not in res:
                        res[player_id] = []
                    if "recipient" in event["pass"] and is_progressive_pass(event) and event["pass"]["recipient"]["id"] in ids:
                        res[player_id].append(event)
                elif team_id in ids:
                    if team_id not in res:
                        res[team_id] = []
                    if "recipient" in event["pass"] and is_progressive_pass(event):
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
