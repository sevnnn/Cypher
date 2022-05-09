import os
import requests
import urllib3
import json
from base64 import b64encode


class Cypher:
    _VERSION = "1.0"
    _MATCHING_VER = True

    # global vars
    lockfile = []
    headers = {}
    agents = {}
    maps = {}
    ranks = {}
    token = puuid = access_token = glz = pd = version = ""
    current_season = "3e47230a-463c-a301-eb7d-67bb60357d4f"

    def __init__(self):
        print("Loading...")
        # disable warning
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # cheking for update
        r = requests.get("https://raw.githubusercontent.com/sevnnn/Cypher/main/VERSION")
        if r.text != self._VERSION:
            self._MATCHING_VER = False

        # getting lockfile
        path = os.getenv("localappdata") + "\\Riot Games\\Riot Client\\Config\\lockfile"
        try:
            with open(path, "r") as f:
                self.lockfile = f.read().split(":")
        except:
            print("[ERROR] Run VALORANT before running Cypher")
            exit()

        # get logs
        path = os.getenv("localappdata") + "\\VALORANT\\Saved\\Logs\\ShooterGame.log"
        with open(path, "r") as f:
            ch1 = ch2 = ch3 = False
            for line in f.readlines():
                line = line.strip()
                if "CI server version:" in line and not ch1:
                    version = line.split(" ")[-1].split("-")
                    version.insert(2, "shipping")
                    self.version = "-".join(version)
                    ch1 = True
                if "https://pd." in line and not ch2:
                    region = line.split("https://pd.")[1].split(".a.pvp.net")
                    self.pd = f"https://pd.{region[0]}.a.pvp.net"
                    ch2 = True
                if "https://glz" in line and not ch3:
                    region = line.split("https://glz")[1].split(".a.pvp.net")[0][1:]
                    self.glz = f"https://glz-{region}.a.pvp.net"
                    ch3 = True
                if ch1 and ch2 and ch3:
                    break

        # get token
        self._regen_token()

        # set headers
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Riot-Entitlements-JWT": self.token,
            "X-Riot-ClientPlatform": "ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9",
            "X-Riot-ClientVersion": self.version,
            "User-Agent": "ShooterGame/13 Windows/10.0.19043.1.256.64bit",
        }

        # get agents
        r = requests.get("https://valorant-api.com/v1/agents?isPlayableCharacter=true")
        for agent in r.json()["data"]:
            self.agents[agent["uuid"]] = agent["displayName"]

        # get maps
        r = requests.get("https://valorant-api.com/v1/maps")
        for map in r.json()["data"]:
            self.maps[map["mapUrl"]] = {
                "displayName": map["displayName"],
                "splash": map["splash"],
            }

        # get ranks
        r = requests.get("https://valorant-api.com/v1/competitivetiers")
        for rank in r.json()["data"][-1]["tiers"]:
            self.ranks[rank["tier"]] = {
                "tierName": rank["tierName"],
                "image": rank["largeIcon"],
            }

        print("Loading complete!")

    def _regen_token(self):
        auth = b64encode(f"riot:{self.lockfile[3]}".encode("ascii")).decode("ascii")
        r = requests.get(
            f"https://127.0.0.1:{self.lockfile[2]}/entitlements/v1/token",
            headers={"Authorization": f"Basic {auth}"},
            verify=False,
        )
        self.access_token = r.json()["accessToken"]
        self.puuid = r.json()["subject"]
        self.token = r.json()["token"]

    def api_get(self, type: str, endpoint: str):
        url = ""
        if type == "glz":
            url = self.glz + endpoint
        if type == "pd":
            url = self.pd + endpoint

        r = requests.get(url, headers=self.headers)

        return r.json(), r.status_code

    def api_put(self, type: str, endpoint: str, payload):
        url = ""
        if type == "glz":
            url = self.glz + endpoint
        if type == "pd":
            url = self.pd + endpoint

        r = requests.put(url, headers=self.headers, json=payload)

        return r.json(), r.status_code

    def gather_info(self, match_body: dict):
        blue = []
        red = []
        map = self.maps[match_body["MapID"]]
        server = match_body["GamePodID"].split("-")[-2].title()
        q = ""
        try:
            q = match_body["MatchmakingData"]["QueueID"].title()
        except:
            q = "Shooting Range"
        for player in match_body["Players"]:
            i = 0
            player_mmr = self.api_get(
                "pd", f"/mmr/v1/players/{player['PlayerIdentity']['Subject']}"
            )[0]
            with open(f"./static/json/test/{i}.json", "w") as f:
                json.dump(player_mmr, f)
                i += 1

            try:
                comp_short = player_mmr["QueueSkills"]["competitive"][
                    "SeasonalInfoBySeasonID"
                ]
                rank = self.ranks[comp_short[self.current_season]["CompetitiveTier"]]
                rr = comp_short[self.current_season]["RankedRating"]
                winrate = ""
                games = ""
                if comp_short[self.current_season]["NumberOfGames"] > 0:
                    winrate = round(
                        comp_short[self.current_season]["NumberOfWins"]
                        / comp_short[self.current_season]["NumberOfGames"]
                        * 100,
                        2,
                    )
                    games = comp_short[self.current_season]["NumberOfGames"]
                else:
                    winrate = 0
                    games = 0
            except:
                rank = self.ranks[0]
                rr = 0
                winrate = 0
                games = 0
                with open("no_games_mmr.json", "w") as f:
                    json.dump(player_mmr, f)

            peak = 0
            try:
                for season in comp_short:
                    if comp_short[season]["CompetitiveTier"] > peak:
                        peak = comp_short[season]["CompetitiveTier"]
            except:
                pass

            username = self.api_put(
                "pd", "/name-service/v2/players", [player["PlayerIdentity"]["Subject"]]
            )[0][0]

            player_info = {
                "PUUID": player["PlayerIdentity"]["Subject"],
                "Agent": player["CharacterID"].lower(),
                "Username": f"{username['GameName']}#{username['TagLine']}",
                "Level": str(player["PlayerIdentity"]["AccountLevel"]),
                "Rank": rank["tierName"],
                "RankImage": rank["image"],
                "RR": rr,
                "Peek": self.ranks[peak]["tierName"],
                "PeekImage": self.ranks[peak]["image"],
                "Winrate": winrate,
                "GamesPlayed": games,
            }

            if player["TeamID"] == "Blue":
                blue.append(player_info)
            else:
                red.append(player_info)

        info = {
            "Map": map["displayName"],
            "MapImage": map["splash"],
            "q": q,
            "Server": server,
        }

        if not self.puuid in str(blue):
            blue, red = red, blue

        return info, blue, red
