import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from ReplayRenamer import ReplayRenamer, RenamerGUI
from loguru import logger
import pytest

path = Path(__file__).parent


def test_rename_replay():
    gui = RenamerGUI()
    gui.load_defaults()
    renamer = ReplayRenamer()

    replay_path = path / "test_replays" / "valid_custom_game_replay.SC2Replay"
    replay = renamer.load_replay(replay_path)
    assert renamer.does_replay_pass_filter(replay, gui.settings)

    target_name: str = renamer.get_replay_rename_name(replay, gui.settings)
    target_path: Path = path / "test_replays" / target_name
    if target_path.is_file():
        os.remove(target_path)
    assert not target_path.is_file()
    renamer.copy_replays({replay_path: target_path}, gui.settings)
    # Cleanup
    assert target_path.is_file()
    os.remove(target_path)


def test_try_renaming_replay_which_doesnt_work():
    renamer = ReplayRenamer()

    replay_path = path / "test_replays" / "invalid_bot_replay.SC2Replay"
    with pytest.raises(IndexError):
        replay = renamer.load_replay(replay_path)
