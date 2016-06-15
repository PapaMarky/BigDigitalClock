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
        'lightsensor': {
            'gain': 0,
            'timing': 3
            },
        'autobright': {
            'sensor_min': 0,
            'sensor_max': 1000,
            'pwm_min': 5,
            'pwm_max': 200
            },
        'brightness': 25,
        'clock': {
            # if True 24hr mode, if False 12hr mode 
            'twenty_four_hour': False,
            'show_seconds': True,
            'show_temperature': False
            }
        }
    def __init__(self, path):
        self.path = path
        self.config = None
        self.load_file()

    def set_brightness(self, b):
        self.config['brightness'] = b
        logger.info('set_brightness(%s)', b)
        self.write_file()

    def get_brightness(self):
        return self.config['brightness']

    def get_autobright(self):
        return self.config['autobright']

    def get_lightsensor(self):
        return self.config['lightsensor']

    def set_mode(self, m):
        self.config['mode'] = m
        logger.info('set_mode(%s)', m)
        self.write_file()

    def get_config(self):
        if self.config is None:
            load_file()

        return self.config

    def write_file(self):
        with open(self.path, 'w') as json_file:
            json.dump(self.config, json_file)

    def merge_dict(self, dict_target, dict_source):
        for key in dict_source:
            if not key in dict_target:
                dict_target[key] = dict_source[key]
            elif isinstance(dict_source[key], dict):
                self.merge_dict(dict_target[key], dict_source[key])
                
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


