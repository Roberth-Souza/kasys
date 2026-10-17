"""Collects current avatar from fastfetch, or config.toml to display on the app"""

import json
import os
import tomllib
from typing import cast

FASTFETCH_PATH = "~/.config/fastfetch/config.jsonc"
KASYS_CONFIG_PATH = "~/.config/kasys/config.toml"
SUPPORTED_IMAGE_FORMATS = {".png", ".jpg", ".jpeg", ".webp"}


def read_config(path: str) -> str | None:
    config = os.path.expanduser(path)
    try:
        with open(config, "r") as raw_config:
            config_content = raw_config.read()
    except OSError:
        return None

    return config_content


def parse_kasys_config(config: str) -> str | None:
    try:
        parsed_config = tomllib.loads(config)
    except tomllib.TOMLDecodeError:
        return None

    avatar = parsed_config.get("avatar")

    if not isinstance(avatar, str):
        return None

    return avatar


def parse_fastfetch_config(config: str) -> str | None:
    try:
        parsed_config = cast(object, json.loads(config))
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed_config, dict):
        return None

    logo = cast(dict[str, object], parsed_config).get("logo")

    if isinstance(logo, str):
        return logo

    if not isinstance(logo, dict):
        return None

    source = cast(dict[str, object], logo).get("source")

    if isinstance(source, str):
        return source

    return None


def resolve_image(path: str) -> str | None:
    full_path = os.path.expanduser(path)
    if not os.path.isfile(full_path):
        return None

    extension = os.path.splitext(full_path)[1].lower()
    if extension not in SUPPORTED_IMAGE_FORMATS:
        return None

    return full_path


def get_kasys_avatar() -> str | None:
    kasys_config = read_config(KASYS_CONFIG_PATH)
    if kasys_config is None:
        return None
    parsed_kasys_config = parse_kasys_config(kasys_config)
    if parsed_kasys_config is None:
        return None
    avatar_path = resolve_image(parsed_kasys_config)
    return avatar_path


def get_fastfetch_avatar() -> str | None:
    fastfetch_config = read_config(FASTFETCH_PATH)
    if fastfetch_config is None:
        return None
    parsed_fastfetch_config = parse_fastfetch_config(fastfetch_config)
    if parsed_fastfetch_config is None:
        return None
    avatar_path = resolve_image(parsed_fastfetch_config)
    return avatar_path


def get_avatar_path() -> str | None:
    avatar = get_kasys_avatar()
    if avatar:
        return avatar

    avatar = get_fastfetch_avatar()
    return avatar


if __name__ == "__main__":
    print(get_avatar_path())
