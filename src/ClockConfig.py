#!/usr/bin/python
# Copyright 2016, Mark Dyer
import os
import json
import logging

logger = logging.getLogger('BigClock.Config')

VALID_MODES = ['off', 'clock']

class ClockConfig:
    DEFAULTS = {
        'mode': 'clock',
        'clock': {
            # if True 24hr mode, if False 12hr mode 
            'twenty_four_hour': False,
            'brightness': 25
            }
        }
    def __init__(self, path):
        self.path = path
        self.config = None
        self.load_file()

    def get_config(self):
        if self.config is None:
            load_file()

        return self.config

    def write_file(self):
        with open(self.path, 'w') as json_file:
            json.dump(self.config, json_file)

    def load_file(self):
        logger.debug('load_file()')

        if not os.path.exists(self.path):
            logger.info('config file missing, creating from DEFAULTS')
            self.config = ClockConfig.DEFAULTS
            self.write_file()
        else:
            with open(self.path) as json_file:
                self.config = json.load(json_file)
            # Merge with defaults

