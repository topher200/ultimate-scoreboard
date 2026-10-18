"""Runs the app from the active OTA slot."""

import microcontroller

import ota_loader


def start():
    from src.board_main import run

    run()


ota_loader.run_app("/", start, microcontroller.reset)
