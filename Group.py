# -*- coding: utf-8 -*-

# Code by Yinzo:        https://github.com/Yinzo
# Origin repository:    https://github.com/Yinzo/SmartQQBot

import cPickle

from QQLogin import *
from Configs import *
from GameConfigs import *
from GameUtil import *
from Msg import *
from HttpClient import *

logging.basicConfig(
    filename='smartqq.log',
    level=logging.DEBUG,
    format='%(asctime)s  %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S',
)


class Group:

    def __init__(self, operator, ip):
        assert isinstance(operator, QQ), "Pm's operator is not a QQ"
        self.__operator = operator
        if isinstance(ip, (int, long, str)):
            # 使用uin初始化
            self.guin = ip
            self.gid = ""
        elif isinstance(ip, GroupMsg):
            self.guin = ip.from_uin
            self.gid = ip.info_seq
        self.msg_id = int(random.uniform(20000, 50000))
        self.member_list = []
        self.msg_list = []
        self.global_config = DefaultConfigs()
        self.private_config = GroupConfig(self)
        self.game_config = GameConfig().conf
        self.game_helper = Game()
        self.update_config()
        self.process_order = [
            "game_test",
            "query_info",
            "daily_sign_in",
            "pet_practice",
            "pet_level_up"
        ]
        logging.info(str(self.gid) + "群已激活, 当前执行顺序： " + str(self.process_order))

    def update_config(self):
        self.private_config.update()
        use_private_config = bool(self.private_config.conf.getint("group", "use_private_config"))
        if use_private_config:
            self.config = self.private_config
        else:
            self.config = self.global_config
        self.config.update()

    def handle(self, msg):
        self.update_config()
        logging.info("msg handling.")
        # 仅关注消息内容进行处理 Only do the operation of handle the msg content
        for func in self.process_order:
            try:
                if bool(self.config.conf.getint("group", func)):
                    logging.info("evaling " + func)
                    if eval("self." + func)(msg):
                        logging.info("msg handle finished.")
                        self.msg_list.append(msg)
                        return func
            except ConfigParser.NoOptionError as er:
                logging.warning(str(er) + "没有找到" + func + "功能的对应设置，请检查共有配置文件是否正确设置功能参数")
        self.msg_list.append(msg)

    def reply(self, reply_content, fail_times=0):
        fix_content = str(reply_content.replace("\\", "\\\\\\\\").replace("\n", "\\\\n").replace("\t", "\\\\t")).decode("utf-8")
        rsp = ""
        try:
            req_url = "http://d.web2.qq.com/channel/send_qun_msg2"
            data = (
                ('r', '{{"group_uin":{0}, "face":564,"content":"[\\"{4}\\",[\\"font\\",{{\\"name\\":\\"Arial\\",\\"size\\":\\"10\\",\\"style\\":[0,0,0],\\"color\\":\\"000000\\"}}]]","clientid":"{1}","msg_id":{2},"psessionid":"{3}"}}'.format(self.guin, self.__operator.client_id, self.msg_id + 1, self.__operator.psessionid, fix_content)),
                ('clientid', self.__operator.client_id),
                ('psessionid', self.__operator.psessionid)
            )
            rsp = HttpClient().Post(req_url, data, self.__operator.default_config.conf.get("global", "connect_referer"))
            rsp_json = json.loads(rsp)
            if rsp_json['retcode'] != 0:
                raise ValueError("reply group chat error" + str(rsp_json['retcode']))
            logging.info("Reply successfully.")
            logging.debug("Reply response: " + str(rsp))
            self.msg_id += 1
            return rsp_json
        except:
            if fail_times < 5:
                logging.warning("Response Error.Wait for 2s and Retrying." + str(fail_times))
                logging.debug(rsp)
                time.sleep(2)
                self.reply(reply_content, fail_times + 1)
            else:
                logging.warning("Response Error over 5 times.Exit.reply content:" + str(reply_content))
                return False

    def format_long_number(self, num, digits = 3, split = " "):
        ret_str = []
        num = int(num)
        base_num = 1
        for i in range(0, digits): base_num = base_num * 10
        while True:
            remain_num = num % base_num
            num = int(num / base_num)
            if num == 0:
                ret_str.append(str(remain_num))
                break
            else:
                ret_str.append("%03d"%remain_num)
        if ret_str:
            ret_str.reverse()
            return split.join(ret_str)
        else:
            return "0"

    def get_user_qq(self, msg):
        return (str(self.__operator.account), str(msg.group_code), str(self.__operator.uin_to_account(msg.send_uin)))

    def game_test(self, msg):
        if str(msg.content).lower().strip(' ') in ["test", "gametest", "game test"]:
            self.reply("我是游戏我是游戏，玩我玩我！")
            return True
        else:
            return False

    def query_info(self, msg):
        msg_content = str(msg.content).strip(' ')
        reply_msg = None
        user_qq = self.get_user_qq(msg)
        user_nick = self.__operator.get_friend_info(msg)['nick']
        if msg_content == "我的宠物":
            pet = self.game_helper.getPet(user_qq = user_qq)
            if pet:
                level_info = self.game_config.levels[pet.level]
                reply_msg = "【{0}】的宠物\n宠物等级：{1}{2}\n当前体力：{3}\n目前积分：{4}".format(user_nick, level_info.grade, level_info.level, pet.power, self.format_long_number(pet.user.score))
                if hasattr(level_info, 'benefits_description') and not level_info.benefits_description == "":
                    reply_msg = reply_msg + '\n' + level_info.benefits_description
            else:
                reply_msg
            self.reply(reply_msg)
            return True
        else:
            return False

    def daily_sign_in(self, msg):
        msg_content = str(msg.content).strip(' ')
        reply_msg = None
        user_qq = self.get_user_qq(msg)
        user_nick = self.__operator.get_friend_info(msg)['nick']
        score_to_add = self.game_config.default.signin_score
        if msg_content == "签到":
            result = self.game_helper.dailySignin(user_qq = user_qq)
            reply_msg = "【{0}】".format(user_nick)
            if result == 0:
                reply_msg += "签到成功！获得 {0} 积分，宠物体力值重设为 {1}。".format(self.format_long_number(score_to_add), self.game_config.default.power)
            elif result == 2:
                reply_msg += "签到失败！今天已经签到过了。"
            elif result == 3:
                reply_msg += "签到失败！积分余额不足。"
            else:
                reply_msg += "签到失败！发生系统错误，请联系管理员。"
            self.reply(reply_msg)
            return True
        else:
            return False

    def pet_practice(self, msg):
        msg_content = str(msg.content).strip(' ')
        reply_msg = None
        user_qq = self.get_user_qq(msg)
        user_nick = self.__operator.get_friend_info(msg)['nick']
        if msg_content == "宠物修炼":
            pet = self.game_helper.getPet(user_qq = user_qq)
            rules = self.game_config.levels[pet.level].practices
            power_cost = self.game_config.default.power_cost_of_practice
            result = self.game_helper.petPractice(pet)
            reply_msg = "【{0}】的宠物".format(user_nick)
            if isinstance(result, list):
                reply_msg += "修炼完成！\n消耗{0}点体力值".format(power_cost)
                has_hit = False
                for i in range(0, len(rules)):
                    score_gotten = result[i]
                    rule_item = rules[i]
                    if score_gotten != 0 and rule_item.score != 0:
                        has_hit = True
                        is_positive = "获得" if rule_item.score > 0 else "损失"
                        if abs(rule_item.score) > 1: reply_msg += "\n{0}了 {1} 点积分".format(is_positive, self.format_long_number(score_gotten))
                        else:
                            if rule_item.condition == "lose":
                                reply_msg += "\n{0}获得了已损失积分中的{1}%，即 {2} 点积分。".format(is_positive, int(rule_item.score * 100), self.format_long_number(score_gotten))
                            else:
                                reply_msg += "\n{0}了 {1} 点积分".format(is_positive, self.format_long_number(score_gotten))
                if not has_hit: reply_msg += "\n什么也没得到"
            elif result == 1:
                reply_msg += "\n体力值不足，无法修炼。"
            else:
                reply_msg += "\n修炼失败，发生系统错误。"
            self.reply(reply_msg)
            return True
        else:
            return False

    def pet_level_up(self, msg):
        msg_content = str(msg.content).strip(' ')
        reply_msg = None
        user_qq = self.get_user_qq(msg)
        user_nick = self.__operator.get_friend_info(msg)['nick']
        if msg_content == "宠物升级":
            pet = self.game_helper.getPet(user_qq = user_qq)
            to_level = pet.level + 1
            score_cost = self.game_config.levels[to_level].score
            result = self.game_helper.petLevelUp(pet)
            reply_msg = "【{0}】的宠物".format(user_nick)
            if result == 0:
                to_level = self.game_config.levels[to_level]
                reply_msg += "升至{0}{1}，消耗了 {2} 积分".format(to_level.grade, to_level.level, self.format_long_number(score_cost))
            elif result == 1:
                reply_msg += "无法升级，积分不够了"
            elif result == 2:
                reply_msg += "已经是满级了哦"
            else:
                reply_msg += "升级失败，发生系统错误"
            self.reply(reply_msg)
            return True
        else:
            return False





