## WORK IN PROGRESS (some features untested)

# StarCraft 2 Replay Renamer

## Installation

### 1) Python variant:

Download and install or newer [Python 3.7](https://www.python.org/downloads/) (only tested on 3.7)

Install requirements 
```
pip install poetry
poetry install
```
Run
```
poetry run python ReplayRenamer.py
```

### 2) Windows only variant:

- Download the `ReplayRenamer.zip` from [here](https://github.com/BurnySc2/SC2-Replay-Renamer/releases)
- Download and launch `ReplayRenamer.exe`

## Features

#### Renaming

You can rename your SC2 replays

```
Para Site LE (61).SC2Replay
```
to a more readable format
```
1v1 2018-12-12 19-58-10 BuRny(T) 5137 vs 5641 (P)llllllllllll - 9 mins on Para Site LE.SC2Replay
``` 
via variables. This example used the following renaming pattern:
```
$gametype $year-$month-$day $hour-$min-$sec $t1names($t1races) $t1mmr vs $t2mmr ($t2races)$t2names - $durationmins mins on $mapname
```

A setting exists that automatically figures out which team won the game and puts that team as team 1 (first listed team).

#### Replay filter system

You can filter by
- Game type
    - Matchmaking
    - Custom games
    - Games with AI
    - Games that end in a draw
    - Games that were resumed from replay
- SC2 Expansions
    - WoL
    - HotS
    - LotV
- Player Names
    - Replays that have certain players in them
    - Replays that do not have certain players in them
- Matchup (same as above)
- Game Version
- Game Length
- Amount of Players
- Average MMR of all players
- Maps

#### Automatic zipping after renaming

After copying / moving / renaming the replays, you can let this tool automatically zip all the copied / moved / renamed replays to `Replays.zip` file.

## Preview

![Preview Image](https://i.imgur.com/u9ZcAx7.png)

## Rename Pattern Configuration

Variable | Example output
:---:|:---:
$expansion | LotV
$EXPANSION | LOTV
$gametype | `1v1` or `2v2` or `FFA`
$playersamount | 4
$mapname | Para Site LE
$durationmins | 9
$durationsecs | 23
$durationtotalsecs | 563
$version | 4.8.0
$region | eu
$REGION | EU
$avgmmr | 3456
$year | 2019
$month | 01
$day | 26
$hour | 18
$minute or $min | 56
$second or $sec | 55
$p1name | BuRny
$p1mmr | 3456 (0 if it wasn't a ladder game)
$p1race | Terran
$p1r | T
$p2name | NotBuRny
$p2mmr | 6543 (0 if it wasn't a ladder game)
$p2race | Zerg
$p2r | Z
$t1names | BuRny NotBuRny
$t1mmr | 5000 (0 if it wasn't a ladder game)
$t1races | TZ
$t2names | BuRnyProtoss NotBurnyRandom
$t2mmr | 5001 (0 if it wasn't a ladder game)
$t2races | PZ

## GUI Element Descriptions

If any filter field with text input is empty, the filter will be ignored.

Element | Example Input | Description
:---:|:---:|:---:|
Rename Pattern | | See above
Replays Folder | `C:/Users/Burny/Documents/StarCraft II/Accounts` | The given replay folder (and its subfolders) will be parsed for replays
Target Folder | `C:/MyReplays` | The target folder where replays will be copied / moved to
Replay File Operation | Copy/Move/Rename | If `Rename` was selected, the `Replays Folder` will be used. If `Copy` or `Move` was selected, replays will be copied/moved and in the `Target Folder` renamed 
Winner is player 1 / team 1 | | If `True`, the winning team / player will be stored in `$p1name` and `$t1names` variables, the loser in `$p2name` and `$t2names`
Enable Filter | | If `False`, all the filters below will be ignored and replays will just be renamed (and copied / moved)
Exclude Matchmaking | | Excludes replays that were played where a queue system was used
Exclude Custom Games | | Exclude replays that were used by hosting games via custom game / arcade
Exclude Games With AI | | Exclude replays that have any AI in it
Exclude Draws | | Exclude replays that ended in a draw
Exclude Resumed from Replay | | Exclude games that were resumed from replay
Expansions | WoL / HotS / LotV | Replays that are not part of the selected expansion will be excluded
Match Names | `BuRny, FakeBuRny` (not case sensitive) | If none of these names is found in the replay, the replay will be excluded
Exclude Names | `Serral, Maru` (not case sensitive) | If any of these names is found in the replay, the replay will be excluded
Game Version | `4.5.0` and `4.8.0` | The given versions mark the minimum and maximum values. This example on the left would only allow replays to be copied/moved/renamed that are between version `4.5.0` and `4.8.0`
Game Length | `3` and `90` | The given game lengths mark the minimum and maximum game duration in minutes. The example on the left would only allow replays between 3 and 90 minutes
Players Amount | `2` and `4` | In this example, only replays between 2 and 4 players are allowed to be copied/moved/renamed
Average MMR | `3000` and `5000` | Only replays where the average player mmr is between 3000 and 5000 is allowed to be parsed. This only works with matchmaking games. If the replay does not come from a matchmaking game, this filter will allow the replay to be parsed.
Include Matchups | `TvX, pvp` (not case sensitive) | Here, all TvX and XvT matchups and the PvP matchup are allowed to be parsed. `ZvZ, ZvP` will be ignored.
Exclude Matchups | `TvZ` | If `TvZ` is entered here and `TvX` in `Include Matchups`, then only `TvP` and `TvT` matchups will be parsed
Exclude Maps | `acid plant, para site` (not case sensitive) | Map names listed here will try to be partially matched with real map names. So writing `para` or `acid` would be enough to exclude all maps that have `acid` or `para` in their name
Show Errors | | Critical errors will be shown regardless, unless it causes the program to crash. Enabling this will just show non-critical errors
Zip Replays after Renaming | | After replays were copied/moved/renamed, all the replays that were parsed will be included in a `Replays.zip` file. The zip will will be located in the `Target Folder`
Rename Replays | | After hitting this button, all the replays will in the `Replays Folder` folder and subfolders will be looked at, filtered, and then copied/moved and finally renamed. After that, they may be zipped if the `Zip Replays after Renaming` option is on












