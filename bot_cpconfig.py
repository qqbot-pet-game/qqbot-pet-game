import sys, os
import getopt
import json

bot_copy_config_options = {
    "src_path": os.path.split(os.path.realpath(__file__))[0] + '/config/game_config.tpl.json',
    "dest_path": os.path.split(os.path.realpath(__file__))[0] + '/config/game_config.json',
    "ignore": []
}

def botCopyConfig(src, dest, ignore = []):
    src_file = open(src)
    src_config = json.load(src_file)
    src_file.close()
    dest_file = open(dest)
    dest_config = json.load(dest_file)
    dest_file.close()
    dest_config = botCopyConfigSingle(src_config, dest_config, ignore = ignore)
    dest_file = open(dest, 'w')
    json.dump(dest_config, dest_file, indent = 4)
    dest_file.close()

def botCopyConfigSingle(src, dest, level_prefix = "", ignore = []):
    if isinstance(src, dict):
        for k,v in src.items():
            if not (level_prefix + k) in ignore:
                dest[k] = botCopyConfigSingle(src[k], dest[k], level_prefix = level_prefix + k + ".", ignore = ignore)
    elif isinstance(src, list):
        if not (level_prefix) in ignore:
            for i in src:
                if i in dest:
                    idx = dest.index(i)
                    dest[idx] = botCopyConfigSingle(i, dest[idx], level_prefix = level_prefix + ".", ignore = ignore)
                else:
                    fake_item = None
                    if isinstance(i, dict): fake_item = {}
                    elif isinstance(i, list): fake_item = []
                    else: fake_item = None
                    dest.append(botCopyConfigSingle(i, fake_item, level_prefix = level_prefix + ".", ignore = ignore))
    else:
        if not level_prefix in ignore:
            dest = src
    return dest

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding("utf-8")
    options, args = getopt.getopt(sys.argv[1:], "s:d:i:", ['src=', 'dest=', 'ignore='])
    for k,v in options:
        if k in ['-s', '--src']:
            bot_copy_config_options['src_path'] = v
        elif k in ['-d', '--dest']:
            bot_copy_config_options['dest_path'] = v
        elif k in ['-i', '--ignore']:
            bot_copy_config_options['ignore'].append(v)
    botCopyConfig(bot_copy_config_options['src_path'], bot_copy_config_options['dest_path'], bot_copy_config_options['ignore'])