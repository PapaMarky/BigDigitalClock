#!/usr/bin/python
# Copyright 2016, Mark Dyer
import json

class ClockConfig:
    DEFAULTS = {
        'clock': {
            # if True 24hr mode, if False 12hr mode 
            'twenty_four_hour': False
            }
        }
    def __init__(self, path):
        self.path = path
        self.config = None

    def get_config():
        if self.config is None:
            load_file()

        return self.config

    def load_file():
        with open(self.path) as json_file:
            self.config = json.load(json_file)

