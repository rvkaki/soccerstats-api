import soccerdata as sd
from statsbombpy import sb
import json
from constants import WorldcupMatchIdToFBRefId, WorldCupFBRefId, WorldCupFBRefSeasonId

match_id = 3869254


def get_player_stats_by_jersey_number(match_id: int, team_name: str, jersey_number: int):
    fbrefMatchId = WorldcupMatchIdToFBRefId[match_id]
    fbref = sd.FBref(leagues=WorldCupFBRefId, seasons=WorldCupFBRefSeasonId)
    stats = fbref.read_player_match_stats(match_id=fbrefMatchId)

    result = {}
    for key, row in stats.iterrows():
        team = key[3]
        if team == team_name and row["jersey_number"][''] == jersey_number:
            result = row["Performance"]
            break

    return result


def main():
    events = sb.events(match_id=match_id, split=True, flatten_attrs=True)
    res = {}
    for key in events.keys():
        res[key] = events[key].to_dict(orient='records')

    print(json.dumps(res, indent=4).replace("NaN", "null"))


main()
