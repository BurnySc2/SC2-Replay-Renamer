import sc2reader
from typing import List, Dict, Set, Optional, Union
import json, re
import PySimpleGUI as sg
import getpass, os, shutil
import zipfile

"""
Replay data variables:

build: int - the current sc2 build version
category: str - the category the game was played in, e.g. "Ladder"
clients: list - list of Participants
    Participant:
        clan_tag: str - the clan tag
        highest_leage: int - max league the player reached in this game mode? 6 = master league
        is_human: bool - if participant is human
        is_observer: bool - if participant is observing
        is_referee: bool - if participant is referee
        name: str - sc2 ingame account name
        pick_race: str - race the player picked at loading screen
        play_race: str - the race the player got in game (e.g. if pick race was random)
        region: str - region it was played in (e.g. "eu")
        result: str - outcome of the game for participant (e.g. "Loss")
        toon_handle: str - "2-S2-1-727565"
        url: str - "http://eu.battle.net/sc2/en/profile/727565/1/BuRny/"
        init_data: dict: {
            "scaled_rating": int - the mmr
        }
competetive: int - if game was in competetive? 1 for true 0 for false
computers: list - list of Computer players
cooperative: int - if game was coop? 1 for true 0 for false
date: datetime - when the game was played/started (same as "end_time"?)
expansion: str - E.g. "LotV"
filename: str - replay path
frames: int - amount of frames this game was long
game_length: Length - same as "length"
    days: int
    hours: int
    mins: int
    secs: int
    seconds: int - the total amount of seconds of the game
game_type: str - e.g. "1v1"
humans: List[Participant] - list of human players
is_ladder: bool
is_private: bool
map_name: str - e.g. "Catalyst LE"
messages: list - List[ChatEvent] -
    frame: int
    player: Participant
    second: int
    text: str
    to_all: bool
ranked: None ??
real_type: str - e.g. "1v1"
region: str - e.g. "eu"
release_string: str - e.g. "4.1.4.61545"
resume_from_replay: bool - if resumed from replay
speed: str - e.g. "Faster"
start_time: datetime - when the game was started
time_zone: float - GMT + X
type: str - e.g. "1v1"
unix_timestamp: int


Renaming pattern variables:

$build: replay.build, "61545"
$category: replay.category, "Ladder", "Private", "Public"
$expansion: replay.expansion, "LotV"
$EXPANSION: replay.expansion.upper(), "LOTV"
$gametype: replay.game_type, "1v1"
$playersamount: len(replay.players), 1, 2, 3
$mapname: replay.map_name
$durationmins: replay.length.mins, 11
$durationsecs: replay.length.secs, 2
$durationtotalsecs: replay.length.seconds, "661"
$version: replay.release_string.split(".")[:-1]
$region: replay.region
$REGION: replay.region.upper()
$avgmmr: average mmr of all players (only works in ranked matchmaking), 0 default

$year
$month
$day
$hour
$min
$sec

$p1name: "Burny"
$p1mmr: "2500"
$p1race: "Zerg"
$p1r: "Z"
"""


def main():
    gui = RenamerGUI()
    gui.run()


class RenamerGUI:
    def __init__(self):
        # Get pc username (for replay file path)
        # self.username = getpass.getuser()
        self.username = os.environ["USERNAME"]
        # print(self.username)

        # Change the look of PySimpleGui
        sg.ChangeLookAndFeel("BrownBlue") # BrownBlue, Dark, Black

        # Settings dictionary
        self.settings: dict = {}
        self.old_settings: dict = {}

        # Program folder
        self.path = os.path.dirname(__file__)
        self.settings_path = os.path.join(self.path, "settings.json")

        # Renamer object
        self.replay_renamer = ReplayRenamer()

    def load_defaults(self):
        self.settings.update({
            "rename_pattern": "$gametype $year-$month-$day $hour-$min-$sec $t1names($t1races) $t1mmr vs $t2mmr ($t2races)$t2names - $durationmins mins on $mapname",
            "source_path": f"C:/Users/{self.username}/Documents/StarCraft II/Accounts",
            "target_path": f"C:/MyReplays",
            "replay_file_operation": "Copy",
            "sort_winner": True,
            "enable_filter": True,
            "exclude_matchmaking": False,
            "exclude_custom_games": False,
            "exclude_games_with_ai": False,
            "exclude_draws": False,
            "exclude_resume_from_replay": False,
            "wol": True,
            "hots": True,
            "lotv": True,
            "match_names": "",
            "exclude_names": "",
            "game_version_min": "",
            "game_version_max": "",
            "game_length_min": "",
            "game_length_max": "",
            "players_min": "",
            "players_max": "",
            "avg_mmr_min": "",
            "avg_mmr_max": "",
            "include_matchups": "",
            "exclude_matchups": "",
            "exclude_maps": "",
            "show_errors": False,
            "zip_replays": False,
        })


    def load_settings(self):
        if os.path.isfile(self.settings_path):
            try:
                with open(self.settings_path) as f:
                    saved_data: dict = json.load(f)
                self.settings.update(saved_data)
            except Exception as e:
                sg.Print(f"Error loading the settings.json:\n{e}")


    def apply_settings_to_gui(self):
        self.window.Fill(self.settings)
        # for element_id, element_value in self.settings.items():
        #     print(f"Updating element {element_id} with value {element_value}")
        #     self.window.FindElement(key=element_id).Update(value=element_value)


    def load_gui_into_settings(self, values: Dict[str, str]):
        self.settings.update(values)


    def save_settings(self):
        if self.old_settings != self.settings:
            # Fix for multiline: keeps appending \n at the end
            if "rename_pattern" in self.settings:
                self.settings["rename_pattern"] = self.settings["rename_pattern"].strip()
            with open(self.settings_path, "w") as f:
                json.dump(self.settings, f, indent=2)
                print("Saved settings")
            self.old_settings = self.settings


    def verify_entered_data(self, values: Dict[str, str]):
        """ Function to check if all the entered GUI data is valid (returns True if parsed successfully. """
        comma_seperated_elements = {"match_names", "exclude_names", "include_matchups", "exclude_matchups", "exclude_maps"}
        number_elements = {"players_min", "players_max", "game_length_min", "game_length_max", "avg_mmr_min", "avg_mmr_max"}

        # Check game version tuple
        if values["game_version_min"] != "" and values["game_version_max"] != "":
            if tuple(values["game_version_min"]) > tuple(values["game_version_max"]):
                low = values["game_version_min"]
                high = values["game_version_max"]
                sg.Print(f"Rightmost game version needs to be higher than the left game version, you entered '{low}' and '{high}'")
                return False

        # Check replay rename pattern
        not_allowed_characters = {"\\", "/", "*", "?", "\"", "<", ">", "|"}
        for character in values["rename_pattern"]:
            if character in not_allowed_characters:
                pattern = values["rename_pattern"]
                sg.Print(f"Character '{character}' not allowed in renaming pattern, not allowed characters: {str(not_allowed_characters)}, your pattern is: {pattern}")
                return False

        # Check comma seperated elements and number elements that need to be converted from string
        for element_id, element_value in values.items():
            if element_value != "" and element_id in number_elements:
                try:
                    _ = self.replay_renamer.convert_string_to_int(element_value)
                except:
                    sg.Print(f"Invalid entered data in field {element_id}, needs to be a number but you entered '{element_value}'")
                    return False

            if element_id in comma_seperated_elements:
                try:
                    _ = self.replay_renamer.split_values(element_value)
                except Exception as e:
                    sg.Print(f"Invalid entered data in field {element_id}, unable to parse value. You entered {element_value}, error:\n{e}")
                    return False
        return True


    def rename_replays(self, values: Dict[str, str]):
        replay_renamer = ReplayRenamer()
        replays_iterator = replay_renamer.load_replays(values["source_path"])

        target_folder_path = values["target_path"]
        if not os.path.isdir(target_folder_path):
            try:
                os.makedirs(target_folder_path)
            except Exception as e:
                sg.Print(f"Could not create target folder: {target_folder_path}, error:\n{e}")
                return

        # Replays path with {replay_source_path: replay_target_path}
        scheduled_replays: Dict[str, str] = {}

        for replay in replays_iterator:
            print(f"Loaded replay: {replay.filename}")
            filter_return_value = replay_renamer.does_replay_pass_filter(replay, values)
            replay_file_name = os.path.basename(replay.filename)
            if filter_return_value is True:
                source_replay_path: str = replay.filename
                if values["replay_file_operation"] == "Rename":
                    source_folder_path = os.path.dirname(source_replay_path)
                    target_file_name = replay_renamer.get_replay_rename_name(replay, values)
                    target_replay_path = os.path.join(source_folder_path, target_file_name)
                else:
                    target_file_name = replay_renamer.get_replay_rename_name(replay, values)
                    target_replay_path = os.path.join(target_folder_path, target_file_name)
                scheduled_replays[source_replay_path] = target_replay_path
            elif values["show_errors"]:
                sg.Print(f"Replay '{replay_file_name}' did not pass the filter because of filter: {filter_return_value}")

        if scheduled_replays:
            # List of replays that were copied / moved / renamed: [path1, path2, path3]
            successful_target_files = []
            if values["replay_file_operation"] == "Copy":
                successful_target_files = self.replay_renamer.copy_replays(scheduled_replays, values)
            elif values["replay_file_operation"] == "Move":
                successful_target_files = self.replay_renamer.move_replays(scheduled_replays, values)
            elif values["replay_file_operation"] == "Rename":
                successful_target_files = self.replay_renamer.rename_replays(scheduled_replays, values)

            if successful_target_files and values["zip_replays"]:
                zip_path = os.path.join(target_folder_path, "Replays.zip")
                self.create_zip_archive(zip_path, successful_target_files)


    def create_zip_archive(self, zip_path: str, files_to_archive: List[str]):
        target_zip_path = zip_path
        count = 1
        while os.path.isfile(target_zip_path):
            target_zip_path = f"{zip_path} ({count})"
            count += 1
        # Would use LZMA for better compression but it takes too long and replays are very compressed already
        # with zipfile.ZipFile(target_zip_path, "w", compression=zipfile.ZIP_LZMA) as f:
        with zipfile.ZipFile(target_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as f:
            for file_path in files_to_archive:
                file_name = os.path.basename(file_path)
                f.write(file_path, arcname=file_name)


    def handle_events(self, event: str, values: Dict[str, str]):
        if event == "rename_replays":
            self.load_gui_into_settings(values)
            self.save_settings()
            if self.verify_entered_data(values):
                self.rename_replays(values)


    def handle_exit(self, event: str, values: Dict[str, str]):
        self.load_gui_into_settings(values)
        self.save_settings()


    def run(self):
        replay_path = f"C:/Users/{self.username}/Documents/StarCraft II/Accounts"
        first_column_width = 22
        two_column_width = 25
        one_column_width = two_column_width * 2 + 2

        self.load_defaults()
        self.load_settings()

        layout = [
            [sg.Text("Rename Pattern", size=(first_column_width, None)), sg.Multiline("", size=(one_column_width, 3), do_not_clear=True, key="rename_pattern")],

            [sg.Text("Replays Folder", size=(first_column_width, None)), sg.InputText(f"{replay_path}", key="source_path", do_not_clear=True, change_submits=True), sg.FolderBrowse("Browse", initial_folder=self.settings["source_path"], target="source_path")],

            [sg.Text("Target Folder", size=(first_column_width, None)), sg.InputText("", do_not_clear=True, key="target_path", change_submits=True), sg.FolderBrowse("Browse", initial_folder=replay_path, target="target_path")],

            [sg.Text("Replay File Operation", size=(first_column_width, None)), sg.InputCombo(["Copy", "Move", "Rename"], key="replay_file_operation", readonly=True)],

            [sg.Checkbox("Team 1 is Winner", key="sort_winner", change_submits=True)],

            [sg.Checkbox("Enable Filter", key="enable_filter", change_submits=True)],
            [sg.Checkbox("Exclude Matchmaking", key="exclude_matchmaking", change_submits=True)],
            [sg.Checkbox("Exclude Custom Games", key="exclude_custom_games", change_submits=True)],
            [sg.Checkbox("Exclude Games with AI", key="exclude_games_with_ai", change_submits=True)],
            [sg.Checkbox("Exclude Draws", key="exclude_draws", change_submits=True)],
            [sg.Checkbox("Exclude Resumed from Replay", key="exclude_resume_from_replay", change_submits=True)],

            [sg.Text("Expansions", size=(first_column_width, None)),
             sg.Checkbox("WoL", key="wol"),
             sg.Checkbox("HotS", key="hots"),
             sg.Checkbox("LotV", key="lotv")],

            [sg.Text("Match Names", size=(first_column_width, None), tooltip="This replay will only be renamed if one of the names is in the replay (not case sensitive)"),
             sg.Input("", key="match_names", do_not_clear=True, change_submits=True, size=(one_column_width, None), tooltip="burny, brain")],

            [sg.Text("Exclude Names", size=(first_column_width, None), tooltip="This replay will only be renamed if none of the names is in the replay (not case sensitive)"),
             sg.Input("", key="exclude_names", do_not_clear=True, change_submits=True, size=(one_column_width, None), tooltip="burny, brain")],

            [sg.Text("Game Version", size=(first_column_width, None)),
             sg.Input("", key="game_version_min", do_not_clear=True, change_submits=True, size=(two_column_width, None), tooltip="4.6.0"),
             sg.Input("", key="game_version_max", do_not_clear=True, change_submits=True, size=(two_column_width, None), tooltip="4.8.2")],

            [sg.Text("Game Length (Minutes)", size=(first_column_width, None)),
             sg.Input("", key="game_length_min", do_not_clear=True, change_submits=True, size=(two_column_width, None), tooltip="3"),
             sg.Input("", key="game_length_max", do_not_clear=True, change_submits=True, size=(two_column_width, None), tooltip="40")],

            [sg.Text("Amount of Players", size=(first_column_width, None)),
             sg.Input("", key="players_min", do_not_clear=True, change_submits=True, size=(two_column_width, None), tooltip="2"),
             sg.Input("", key="players_max", do_not_clear=True, change_submits=True, size=(two_column_width, None), tooltip="8")],

            [sg.Text("Average MMR", size=(first_column_width, None)),
             sg.Input("", key="avg_mmr_min", do_not_clear=True, change_submits=True, size=(two_column_width, None), tooltip="3500"),
             sg.Input("", key="avg_mmr_max", do_not_clear=True, change_submits=True, size=(two_column_width, None), tooltip="4500")],

            [sg.Text("Include Matchups", size=(first_column_width, None)),
             sg.Input("", key="include_matchups", do_not_clear=True, change_submits=True, size=(one_column_width, None), tooltip="tvz, pvx")],

            [sg.Text("Exclude Matchups", size=(first_column_width, None)),
             sg.Input("", key="exclude_matchups", do_not_clear=True, change_submits=True, size=(one_column_width, None), tooltip="zvx, tvt")],


            [sg.Text("Exclude Maps", size=(first_column_width, None)),
             sg.Input("", key="exclude_maps", do_not_clear=True, change_submits=True, size=(one_column_width, None), tooltip="catalyst, neon violet")],

            [sg.Checkbox("Show Errors", key="show_errors")],

            [sg.Checkbox("Zip Replays after Renaming", key="zip_replays")],

            [sg.Button("Rename Replays", key="rename_replays"), sg.Button("Exit", key="exit")]
        ]

        self.window = sg.Window("Replay Renamer").Layout(layout)

        # Required so settings can be applied (checkboxes are missing when this method is missing)
        self.window.Finalize()

        # Load settings before going into event loop
        self.apply_settings_to_gui()

        while True:
            # Event Loop
            event, values = self.window.Read()

            print(event, values)
            if event is None or event == "exit":
                self.handle_exit(event, values)
                break
            else:
                self.handle_events(event, values)

        self.window.Close()


class ReplayRenamer:
    def __init__(self):
        self.settings = {}
        self.renamer_path = os.path.dirname(__file__)

    def load_replay(self, replay_path):
        """ Loads a single replay """
        return sc2reader.load_replay(replay_path, load_level=2, load_map=False)

    def load_replays(self, folder_path):
        """ Loads multiple replays as generator """
        return sc2reader.load_replays(folder_path, load_level=2, load_map=False)

    def convert_string_to_int(self, string: str) -> int:
        return int(float(string.strip()))

    def split_values(self, string: str) -> Set[str]:
        return {x.strip().lower() for x in string.strip().split(",")}

    def convert_matchup_string(self, string: str) -> List[str]:
        """ Input "TXvZX" becomes ["TX", "XZ"]
            Input "TvX" becomes ["T", "X"] """
        split = string.lower().split("v")
        first = "".join(sorted(split[0])).upper()
        second = "".join(sorted(split[1])).upper()
        return [first, second]

    def match_matchup(self, matchup: List[str], valid_matchups: List[List[str]]) -> bool:
        """ Matches ["T", "P"] with [["T", "X"]]
            and ["TZ", "ZP"] with [["XX", "XZ"]] """
        assert len(matchup) == 2
        for valid_matchup in valid_matchups:
            matchup1, matchup2 = matchup
            valid1, valid2 = valid_matchup
            if len(matchup1) != len(valid1): continue
            if len(matchup2) != len(valid2): continue

            is_valid_match1 = (all(v == "X" or m == v for m, v in zip(matchup1, valid1))
                               and all(v == "X" or m == v for m, v in zip(matchup2, valid2)))
            is_valid_match2 = (all(v == "X" or m == v for m, v in zip(matchup2, valid1))
                               and all(v == "X" or m == v for m, v in zip(matchup1, valid2)))
            if is_valid_match1 or is_valid_match2:
                return True
        return False


    def does_replay_pass_filter(self, replay: "Replay", values: Dict[str, str]) -> Union[bool, str]:
        if values["enable_filter"]:
            if values["exclude_matchmaking"] and replay.is_ladder:
                return "Exclude Matchmaking"
            if values["exclude_custom_games"] and replay.is_private:
                return "Exclude Custom Games"
            if values["exclude_games_with_ai"] and len(replay.computers) > 0:
                return "Exclude Games with AI"
            if values["exclude_resume_from_replay"] and replay.resume_from_replay:
                return "Exclude Resume from Replay"
            if not values["wol"] and replay.expansion.lower() == "wol":
                return "WoL"
            if not values["hots"] and replay.expansion.lower() == "hots":
                return "HotS"
            if not values["lotv"] and replay.expansion.lower() == "lotv":
                return "LotV"

            if values["match_names"] != "":
                split_names = self.split_values(values["match_names"])
                at_least_one_player_found = any(player.name.lower() in split_names for player in replay.players)
                if not at_least_one_player_found:
                    return "Match Names"

            if values["exclude_names"] != "":
                split_names = self.split_values(values["exclude_names"])
                at_least_one_player_found = any(player.name.lower() in split_names for player in replay.players)
                if at_least_one_player_found:
                    return "Exclude Names"

            if values["game_version_min"] != "" or values["game_version_max"] != "":
                release_tuple = tuple(replay.release_string)
                min_value = values["game_version_min"]
                max_value = values["game_version_max"]
                if not ((min_value == "" or tuple(min_value) <= release_tuple)
                    and (max_value == "" or release_tuple <= tuple(max_value))):
                    return "Game Version"

            conv = self.convert_string_to_int
            if values["game_length_min"] != "" or values["game_length_max"] != "":
                game_length = replay.length.mins + replay.length.secs / 60
                min_value = values["game_length_min"]
                max_value = values["game_length_max"]
                if not ((min_value == "" or conv(min_value) <= game_length) and (max_value == "" or game_length <= conv(max_value))):
                    return "Game Length"

            if values["players_min"] != "" or values["players_max"] != "":
                players_amount = len(replay.players)
                min_value = values["players_min"]
                max_value = values["players_max"]
                if not ((min_value == "" or conv(min_value) <= players_amount) and (max_value == "" or players_amount <= conv(max_value))):
                    return "Game Length"

            if values["avg_mmr_min"] != "" or values["avg_mmr_max"] != "" and len(replay.teams) >= 2:
                avg_mmr = sum(player.init_data.get("scaled_rating", 0) or 0 if hasattr(player, "init_data") else 0 for player in replay.players) / len(replay.players)
                min_value = values["avg_mmr_min"]
                max_value = values["avg_mmr_max"]
                if avg_mmr != 0 and not ((min_value == "" or conv(min_value) <= avg_mmr) and (max_value == "" or avg_mmr <= conv(max_value))):
                    return "Average MMR"

            if len(replay.teams) == 2 and len(replay.players) == 2:
                races_team1 = "".join(sorted(replay.teams[0].lineup))
                races_team2 = "".join(sorted(replay.teams[1].lineup))
                matchup = [races_team1, races_team2]
                if values["include_matchups"] != "":
                    # Convert "TvX, ZvX" to [["T", "X"], ["Z", "X"]]
                    # Or "TXvZX" to [["TX", "XZ"]] <- XZ because sorting alphabetically
                    comma_seperated_matchups = self.split_values(values["include_matchups"])
                    valid_matchups = [self.convert_matchup_string(x) for x in comma_seperated_matchups]
                    is_match = self.match_matchup(matchup, valid_matchups)
                    if not is_match:
                        return "Include Matchups"

                if values["exclude_matchups"] != "":
                    comma_seperated_matchups = self.split_values(values["exclude_matchups"])
                    valid_matchups = [self.convert_matchup_string(x) for x in comma_seperated_matchups]
                    is_match = self.match_matchup(matchup, valid_matchups)
                    if is_match:
                        return "Exclude Matchups"

            if values["exclude_maps"] != "":
                comma_seperated_maps = self.split_values(values["exclude_maps"])
                is_match = any(map_name.lower() in replay.map_name.lower() for map_name in comma_seperated_maps)
                if is_match:
                    return "Exclude Maps"
        return True


    def get_replay_values(self, replay: "Replay", values: Dict[str, str]) -> dict:
        # print(hasattr(replay.players[0], "init_data"))
        # print(hasattr(replay.players[1], "init_data"))
        player_data = []
        player_data.append([
            # Player name
            replay.players[0].name,
            # Player mmr, computers dont have "init_data" and it can be "None" if it wasn't a ranked game
            replay.players[0].init_data.get("scaled_rating", 0) or 0 if hasattr(replay.players[0], "init_data") else 0,
            # Player race
            replay.players[0].play_race])
        if len(replay.players) > 1:
            player_data.append([replay.players[1].name,
                 replay.players[1].init_data.get("scaled_rating", 0) or 0 if hasattr(replay.players[1], "init_data") else 0,
                 replay.players[1].play_race])
        else:
            player_data.append(["None", 0, "None"])

        team_data = []
        team_data.append([
                # Player names
                " ".join(player.name for player in replay.teams[0].players),
                # Sum of player mmr
                sum(player.init_data.get("scaled_rating", 0) or 0 if hasattr(player, "init_data") else 0 for player in replay.teams[0].players) // len(replay.teams[0].players),
                # Races in short (e.g. "TZPT")
                replay.teams[0].lineup
            ])
        if len(replay.teams) > 1:
            team_data.append([
                    " ".join(player.name for player in replay.teams[1].players),
                    sum(player.init_data.get("scaled_rating", 0) or 0 if hasattr(player, "init_data") else 0 for player in replay.teams[1].players) // len(replay.teams[1].players),
                    replay.teams[1].lineup
                ])
        else:
            team_data.append(["", 0, ""])

        return {
            "$build": replay.build,
            "$category": replay.category,
            "$expansion": replay.expansion,
            "$EXPANSION": replay.expansion.upper(),
            "$gametype": replay.real_type,
            # "$gametype": replay.game_type,
            "$playersamount": len(replay.players),
            "$mapname": replay.map_name,
            "$durationmins": replay.length.mins,
            "$durationsecs": f"{replay.length.secs:02d}",
            "$durationtotalsecs": replay.length.seconds,
            "$version": ".".join(replay.release_string.split(".")[:-1]),
            "$region": replay.region,
            "$REGION": replay.region.upper(),
            "$avgmmr": sum(player.init_data.get("scaled_rating", 0) or 0 if hasattr(player, "init_data") else 0 for player in replay.players) // len(replay.players) if len(replay.players) > 0 else 0,
            "$year": f"{replay.start_time.year:02d}",
            "$month": f"{replay.start_time.month:02d}",
            "$day": f"{replay.start_time.day:02d}",
            "$hour": f"{replay.start_time.hour:02d}",
            "$min": f"{replay.start_time.minute:02d}",
            "$minute": f"{replay.start_time.minute:02d}",
            "$sec": f"{replay.start_time.second:02d}",
            "$second": f"{replay.start_time.second:02d}",

            # Player data
            "$p1name": player_data[replay.winner.number - 1][0] if replay.winner and values["sort_winner"] else player_data[0][0],
            "$p1mmr": player_data[replay.winner.number - 1][1] if replay.winner and values["sort_winner"] else player_data[0][1],
            "$p1race": player_data[replay.winner.number - 1][2] if replay.winner and values["sort_winner"] else player_data[0][2],
            "$p1r": player_data[replay.winner.number - 1][2][0] if replay.winner and values["sort_winner"] else player_data[0][2][0],

            "$p2name": player_data[2 - replay.winner.number][0] if replay.winner and values["sort_winner"] else player_data[1][0],
            "$p2mmr": player_data[2 - replay.winner.number][1] if replay.winner and values["sort_winner"] else player_data[1][1],
            "$p2race": player_data[2 - replay.winner.number][2] if replay.winner and values["sort_winner"] else player_data[1][2],
            "$p2r": player_data[2 - replay.winner.number][2][0] if replay.winner and values["sort_winner"] else player_data[1][2][0],

            # Team data
            "$t1names": team_data[replay.winner.number - 1][0] if replay.winner and values["sort_winner"] else team_data[0][0],
            "$t1mmr": team_data[replay.winner.number - 1][1] if replay.winner and values["sort_winner"] else team_data[0][1],
            "$t1races": team_data[replay.winner.number - 1][2] if replay.winner and values["sort_winner"] else team_data[0][2],

            "$t2names": team_data[2 - replay.winner.number][0] if replay.winner and values["sort_winner"] else team_data[1][0],
            "$t2mmr": team_data[2 - replay.winner.number][1] if replay.winner and values["sort_winner"] else team_data[1][1],
            "$t2races": team_data[2 - replay.winner.number][2] if replay.winner and values["sort_winner"] else team_data[1][2],
        }


    def get_replay_rename_name(self, replay: "Replay", values: Dict[str, str]) -> str:
        replay_info = self.get_replay_values(replay, values)
        replay_target_name = values["rename_pattern"].strip()
        for variable, value in replay_info.items():
            replay_target_name = replay_target_name.replace(variable, str(value))
        return replay_target_name + ".SC2Replay"


    def copy_replays(self, replay_path_dict: Dict[str, str], values: Dict[str, str]):
        successfully_copied_files = []
        for source_path, target_path in replay_path_dict.items():
            if os.path.isfile(target_path):
                base_name = os.path.basename(source_path)
                if values["show_errors"]:
                    sg.Print(f"Could not copy file '{base_name}' because it already exists in target folder '{target_path}'")
                continue
            shutil.copy2(source_path, target_path)
            successfully_copied_files.append(target_path)
        return successfully_copied_files


    def move_replays(self, replay_path_dict: Dict[str, str], values: Dict[str, str]):
        successfully_moved_files = []
        for source_path, target_path in replay_path_dict.items():
            if os.path.isfile(target_path):
                base_name = os.path.basename(source_path)
                if values["show_errors"]:
                    sg.Print(f"Could not move file '{base_name}' because it already exists in target folder '{target_path}'")
                continue
            shutil.move(source_path, target_path)
            successfully_moved_files.append(target_path)
        return successfully_moved_files


    def rename_replays(self, replay_path_dict: Dict[str, str], values: Dict[str, str]):
        successfully_renamed_files = []
        for source_path, target_path in replay_path_dict.items():
            if os.path.isfile(target_path):
                base_name = os.path.basename(source_path)
                if values["show_errors"]:
                    sg.Print(f"Could not rename file '{base_name}' because it already exists in target folder '{target_path}'")
                continue
            shutil.move(source_path, target_path)
            successfully_renamed_files.append(target_path)
        return successfully_renamed_files


if __name__ == "__main__":
    main()
