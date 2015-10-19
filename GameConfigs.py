import json
import os

from Configs import DefaultConfigs

def convert_dict_to_object(_dict):
    if isinstance(_dict, dict):
        ret_obj = GameConfigObject()
        for k, v in _dict.iteritems():
            setattr(ret_obj, k, convert_dict_to_object(v))
        return ret_obj
    elif isinstance(_dict, list):
        ret_obj = []
        for v in _dict:
            ret_obj.append(convert_dict_to_object(v))
        return ret_obj
    else:
        return _dict

class GameConfig:
    def __init__(self, config_path = None):
        self.global_config = DefaultConfigs()
        self.config_path = config_path if config_path else (os.path.split(os.path.realpath(__file__))[0] + '/' + self.global_config.conf.get("global", "game_config"))
        config_file = open(self.config_path)
        self.conf_dict = json.load(config_file)
        config_file.close()
        self.conf = convert_dict_to_object(self.conf_dict)

class GameConfigObject:
    def __init__(self):
        pass