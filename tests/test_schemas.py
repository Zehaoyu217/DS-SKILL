import json
import pathlib

import pytest
from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text())


def test_state_valid_fixture_validates() -> None:
    schema = load("templates/state.schema.json")
    Draft202012Validator(schema).validate(load("tests/fixtures/state_valid.json"))


def test_state_invalid_fixture_rejected() -> None:
    schema = load("templates/state.schema.json")
    with pytest.raises(Exception):
        Draft202012Validator(schema).validate(load("tests/fixtures/state_invalid.json"))


def test_leaderboard_valid_fixture_validates() -> None:
    schema = load("templates/leaderboard.schema.json")
    Draft202012Validator(schema).validate(load("tests/fixtures/leaderboard_valid.json"))


def test_leaderboard_invalid_fixture_rejected() -> None:
    schema = load("templates/leaderboard.schema.json")
    with pytest.raises(Exception):
        Draft202012Validator(schema).validate(load("tests/fixtures/leaderboard_invalid.json"))
