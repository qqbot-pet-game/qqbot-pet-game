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

import re
import datetime, time

reload(sys)
sys.setdefaultencoding("utf-8")

root_path = os.path.split(os.path.realpath(__file__))[0] + '/'

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
        f = open(root_path + '/' + self.global_config.conf.get('global', 'face_config'))
        self.face_codes = json.load(f)
        f.close()
        self.game_helper = Game(self, config_path = self.__operator.sys_paras['config_path'])
        self.game_config = self.game_helper.game_config
        self.update_config(game = False)
        self.error_msg = self.game_config.default.error_msg
        self.process_order = [
            "game_test",
            "game_help",
            "query_info",
            "daily_sign_in",
            "pet_practice",
            "pet_level_up",
            "pet_work",
            "gamble_fqzs",
            "gamble_sx",
            "gamble_ggl",
            "admin"
        ]
        self.user_nicks = []
        logging.info(str(self.gid) + "群已激活, 当前执行顺序： " + str(self.process_order))

    def update_config(self, game = True):
        self.private_config.update()
        use_private_config = bool(self.private_config.conf.getint("group", "use_private_config"))
        if use_private_config:
            self.config = self.private_config
        else:
            self.config = self.global_config
        self.config.update()

        if game:
            self.game_helper.update_config()
            self.game_config = self.game_helper.game_config

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
            except Exception, e:
                logging.warning("Handle group message error")
        self.msg_list.append(msg)

    def reply(self, reply_content, fail_times=0):
        fix_content = str(reply_content.replace("\\", "\\\\\\\\").replace("\n", "\\\\n").replace("\t", "\\\\t"))
        for face_item in self.face_codes:
            fix_content = fix_content.replace('[{0}]'.format(face_item['name']), '\\",[\\"face\\", {0}],\\"'.format(face_item['code']))
        fix_content = fix_content.decode("utf-8")
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

    def parse_time_period(self, time_period):
        hours = int(time_period)
        milliseconds = hours % 1000
        hours = int(hours / 1000)
        seconds = hours % 60
        hours = int(hours / 60)
        minutes = hours % 60
        hours = int(hours / 60)
        return (hours, minutes, seconds, milliseconds)

    def format_time_period(self, time_period, digits = 1, fmt = None):
        if not isinstance(time_period, tuple):
            time_period = self.parse_time_period(time_period)
        if fmt:
            fmt = fmt.replace('H', 'h')
            fmt = fmt.replace('M', 'm')
            fmt = fmt.replace('S', 's')
            fmt = fmt.replace('W', 'w')
            fmt = fmt.replace('h', '%d'%time_period[0])
            fmt = fmt.replace('mm', '%02d'%time_period[1])
            fmt = fmt.replace('m', '%d'%time_period[1])
            fmt = fmt.replace('ss', '%02d'%time_period[2])
            fmt = fmt.replace('s', '%d'%time_period[2])
            fmt = fmt.replace('www', '%03d'%time_period[3])
            fmt = fmt.replace('ww', '%02d'%time_period[3])
            fmt = fmt.replace('w', '%d'%time_period[3])
            return fmt
        else:
            start_idx = -1
            for t in time_period:
                start_idx += 1
                if t != 0: break
            fmt = ["h小时", "m分钟", "s秒", "w毫秒"][start_idx:start_idx+digits]
            return self.format_time_period(time_period, fmt = "".join(fmt))

    def get_user_qq(self, msg):
        grouo_info = self.__operator.get_group_info(msg)
        if not grouo_info: return None
        if not 'nid' in grouo_info: return None
        return (str(self.__operator.account), grouo_info['nid'], str(self.__operator.uin_to_account(msg.send_uin)))

    def get_user_nick(self, msg):
        info = self.__operator.get_friend_info(msg)
        if not info: return None
        return info['nick']

    def update_user_nick(self, user_nick, user_id = None, user_qq = None):
        user = self.game_helper.getUser(user_id = user_id, user_qq = user_qq)
        user_nick_item = self.game_helper.getItemFromListByProperty(self.user_nicks, 'id', user.id)
        if user_nick_item: user_nick_item['nick'] = user_nick
        else: self.user_nicks.append({'id': user.id, 'nick': user_nick})

    def game_test(self, msg):
        if (not self.__operator.sys_paras['debug']) and (not msg.group_code in self.game_config.default.admin_gcodes):
            return True
        elif str(msg.content).lower().strip(' ') in ["test", "gametest", "game test"]:
            self.reply("我是游戏我是游戏，玩我玩我！")
            return True
        else:
            return False

    def game_help(self, msg):
        msg_content = str(msg.content).strip(' ')
        reply_msg = None
        help_config = self.game_config.help_messages
        help_menu_config = self.game_helper.getItemFromListByProperty(help_config, "name", "menu")
        match = re.compile("({0})".format("|".join([item.face.replace('?', '\\?') for item in help_config]))).match(msg_content)
        if msg_content == help_menu_config.face:
            reply_msg = help_menu_config.message
            self.reply(reply_msg)
            return True
        elif not match is None:
            face = match.group(1)
            item = self.game_helper.getItemFromListByProperty(help_config, "face", face)
            if item is None: return False
            reply_msg = item.message
            self.reply(reply_msg)
            return True
        else:
            return False

    def query_info(self, msg):
        msg_content = str(msg.content).strip(' ')
        reply_msg = None
        user_qq = self.get_user_qq(msg)
        user_nick = self.get_user_nick(msg)
        if msg_content == "我的宠物":
            if (user_qq is None) or (user_nick is None):
                self.reply(self.error_msg)
                return True
            pet = self.game_helper.getPet(user_qq = user_qq)
            if pet:
                level_info = self.game_config.levels[pet.level]
                reply_msg = "【{0}】的宠物\n宠物等 级：{1}{2}\n当前体力：{3}\n目前积 分：{4}".format(user_nick, 
                    level_info.grade, 
                    level_info.level, 
                    pet.power, 
                    self.format_long_number(pet.user.score))
                if hasattr(level_info, 'earning') and not level_info.earning == 0:
                    reply_msg = reply_msg + "\n每打工{0}可得 {1} 分工资".format(self.format_time_period(self.game_config.default.work_interval*1000), 
                        self.format_long_number(self.game_config.levels[pet.level].earning))
                if hasattr(level_info, 'benefits_description') and not level_info.benefits_description == "":
                    reply_msg = reply_msg + '\n' + level_info.benefits_description
            else:
                reply_msg = self.error_msg
            self.reply(reply_msg)
            return True
        elif msg_content == "我的积分":
            if (user_qq is None) or (user_nick is None):
                self.reply(self.error_msg)
                return True
            user = self.game_helper.getUser(user_qq = user_qq)
            if user:
                reply_msg = "【{0}】目前积 分：{1}".format(user_nick, self.format_long_number(user.score))
            else:
                reply_msg = self.error_msg
            print reply_msg
            self.reply(reply_msg)
            return True
        else:
            return False

    def daily_sign_in(self, msg):
        msg_content = str(msg.content).strip(' ')
        reply_msg = None
        user_qq = self.get_user_qq(msg)
        user_nick = self.get_user_nick(msg)
        score_to_add = self.game_config.default.signin_score
        match = re.compile('({0})?签到'.format('|'.join([item.face for item in self.game_config.monthcards]))).match(msg_content)
        if match:
            monthcard_face = match.group(1)
            monthcard_item = self.game_helper.getMonthcard(monthcard_face)
            if monthcard_item: score_to_add = monthcard_item.score
            if (user_qq is None) or (user_nick is None):
                self.reply(self.error_msg)
                return True
            result = self.game_helper.dailySignin(user_qq = user_qq, monthcard_face = monthcard_face)
            reply_msg = "【{0}】".format(user_nick)
            if result == 0:
                if monthcard_face: reply_msg += "使用" + monthcard_face
                reply_msg += "签到成功！获得 {0} 积 分，宠物体力值重设为 {1}。".format(self.format_long_number(score_to_add), self.game_config.default.power)
            elif result == 2:
                reply_msg += "签到失败！今天已经签到过了。"
            elif result == 3:
                reply_msg += "签到失败！积 分 余 额 不足。"
            elif result == 5:
                reply_msg += "还没有办(/TДT)/理{0}或{0}已过期！".format(monthcard_face)
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
        user_nick = self.get_user_nick(msg)
        if msg_content == "宠物修炼":
            if (user_qq is None) or (user_nick is None):
                self.reply(self.error_msg)
                return True
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
                        if abs(rule_item.score) > 1: reply_msg += "\n{0}了 {1} 点积 分".format(is_positive, self.format_long_number(score_gotten))
                        else:
                            if rule_item.condition == "lose":
                                reply_msg += "\n{0}获得了已损失积分中的{1}%，即 {2} 点积 分。".format(is_positive, int(rule_item.score * 100), self.format_long_number(score_gotten))
                            else:
                                reply_msg += "\n{0}了 {1} 点积 分".format(is_positive, self.format_long_number(score_gotten))
                if not has_hit: reply_msg += "\n什么也没得到"
            elif result == 1:
                reply_msg += "\n体力值不足，无法修炼。"
            else:
                reply_msg += "\n修炼失败，发生 系 统 错 误。"
            self.reply(reply_msg)
            return True
        else:
            return False

    def pet_level_up(self, msg):
        msg_content = str(msg.content).strip(' ')
        reply_msg = None
        user_qq = self.get_user_qq(msg)
        user_nick = self.get_user_nick(msg)
        if msg_content == "宠物升级":
            if (user_qq is None) or (user_nick is None):
                self.reply(self.error_msg)
                return True
            pet = self.game_helper.getPet(user_qq = user_qq)
            to_level = pet.level + 1
            score_cost = self.game_config.levels[to_level].score
            result = self.game_helper.petLevelUp(pet)
            reply_msg = "【{0}】的宠物".format(user_nick)
            if result == 0:
                to_level = self.game_config.levels[to_level]
                reply_msg += "升至{0}{1}，消耗了 {2} 积 分".format(to_level.grade, to_level.level, self.format_long_number(score_cost))
            elif result == 1:
                reply_msg += "无法 升 级，积 分 不够了"
            elif result == 2:
                reply_msg += "已经是 满 级 了哦"
            else:
                reply_msg += "升 级 失败，发生系统错误"
            self.reply(reply_msg)
            return True
        else:
            return False

    def pet_work(self, msg):
        msg_content = str(msg.content).strip(' ')
        reply_msg = None
        user_qq = self.get_user_qq(msg)
        user_nick = self.get_user_nick(msg)
        if msg_content == "宠物打工":
            if (user_qq is None) or (user_nick is None):
                self.reply(self.error_msg)
                return True
            pet = self.game_helper.getPet(user_qq = user_qq)
            work_interval = self.game_config.default.work_interval * 1000
            result = self.game_helper.petWorkStart(pet)
            reply_msg = "【{0}】的宠物".format(user_nick)
            if result == 0:
                reply_msg += "开始打工，请{0}后发送“宠物下班”。".format(self.format_time_period(work_interval))
            elif result == 1:
                reply_msg += "正在打工，请先让宠物下班"
            elif result == 2:
                reply_msg += "目前还不能打工，请先 升 级 宠物"
            else:
                reply_msg += "打工失败，发生系统错误"
            self.reply(reply_msg)
            return True
        elif msg_content == "宠物下班":
            if (user_qq is None) or (user_nick is None):
                self.reply(self.error_msg)
                return True
            pet = self.game_helper.getPet(user_qq = user_qq)
            work_earning = self.game_config.levels[pet.level].earning
            work_interval = self.game_config.default.work_interval * 1000
            result = self.game_helper.petWorkEnd(pet)
            reply_msg = "【{0}】的宠物".format(user_nick)
            if result == 0:
                reply_msg += "下班啦～\n领到了 {0} 积 分 工资".format(self.format_long_number(work_earning))
            elif result == 1:
                reply_msg += "并没有在打工"
            elif result == 2:
                reply_msg += "还没打够{0}的工，请稍后再试".format(self.format_time_period(work_interval))
            else:
                reply_msg += "下班失败，发生系统错误"
            self.reply(reply_msg)
            return True
        else:
            return False

    def gamble_fqzs(self, msg):
        msg_content = str(msg.content).strip(' ')
        reply_msg = None
        user_qq = self.get_user_qq(msg)
        user_nick = self.get_user_nick(msg)
        game_config = self.game_config.gambles.fqzs
        pour_match = re.compile('押({0})(\d+)'.format('|'.join([str(prize.name) for prize in game_config.prizes]))).match(msg_content)
        if msg_content == "飞禽走兽":
            if (user_qq is None) or (user_nick is None):
                self.reply(self.error_msg)
                return True
            result = self.game_helper.gambleFqzsStart(user_qq = user_qq)
            if result == 0:
                reply_msg = "飞禽走兽已开局，将于{0}后结束".format(self.format_time_period(game_config.time * 1000))
                for prize in game_config.prizes:
                    reply_msg += "\n{0}   1赔{1}".format(prize.name, prize.rate - 1)
            elif result == 1:
                reply_msg = "当前正在进行其他游戏，请等待游戏结束后再开局"
            else:
                reply_msg = "无法开局，发生系统错误"
            self.reply(reply_msg)
            return True
        elif pour_match:
            face = pour_match.group(1)
            score = int(pour_match.group(2))
            self.update_user_nick(user_nick, user_qq = user_qq)
            result = self.game_helper.gambleFqzsPour(face, score, user_qq = user_qq)
            reply_msg = ""
            if result == 0:
                reply_msg = "【{0}】押了 {1} 分给{2}".format(user_nick, self.format_long_number(score), face)
            elif result == 1:
                return False
            elif result == 3:
                reply_msg = "【{0}】下 注 失败，积 分 不足".format(user_nick)
            else:
                if result == 2: print "invalid face"
                reply_msg = "【{0}】下 注 失败，发生系统错误".format(user_nick)
            self.reply(reply_msg)
            return True
        else:
            return False
    def gamble_fqzs_end(self, face, result):
        reply_msg = "飞禽走兽结束了，本局开奖为：{0}".format(face)
        for item in result:
            user_nick = self.game_helper.getItemFromListByProperty(self.user_nicks, 'id', item['user_id'])
            if user_nick: 
                user_nick = user_nick['nick']
                if item['earning'] > 0:
                    reply_msg += "\n[Cheers]【{0}】赢得了 {1} 积 分".format(user_nick, self.format_long_number(item['earning']))
                elif item['earning'] < 0:
                    reply_msg += "\n[BlowUp]【{0}】输掉了 {1} 积 分".format(user_nick, self.format_long_number(-item['earning']))
                else:
                    reply_msg += "\n[Lolly]【{0}】押得四平八稳，没赔也没赚。".format(user_nick)
        self.reply(reply_msg)

    def gamble_sx(self, msg):
        msg_content = str(msg.content).strip(' ')
        reply_msg = None
        user_qq = self.get_user_qq(msg)
        user_nick = self.get_user_nick(msg)
        game_config = self.game_config.gambles.sx
        pour_match = re.compile('押({0})(\d+)'.format('|'.join([str(prize.name) for prize in game_config.prizes]))).match(msg_content)
        if msg_content == "十二生肖":
            if (user_qq is None) or (user_nick is None):
                self.reply(self.error_msg)
                return True
            result = self.game_helper.gambleSxStart(user_qq = user_qq)
            if result == 0:
                reply_msg = "十二生肖已开局，将于{0}后结束".format(self.format_time_period(game_config.time * 1000))
                for prize in game_config.prizes:
                    if prize.type == "sx": reply_msg += "\n{0}  {1}".format(prize.name, "  ".join([("%02d" % number) for number in prize.numbers]))
            elif result == 1:
                reply_msg = "当前正在进行其他游戏，请等待游戏结束后再开局"
            else:
                reply_msg = "无法开局，发生系统错误"
            self.reply(reply_msg)
            return True
        elif pour_match:
            face = pour_match.group(1)
            score = int(pour_match.group(2))
            self.update_user_nick(user_nick, user_qq = user_qq)
            result = self.game_helper.gambleSxPour(face, score, user_qq = user_qq)
            reply_msg = ""
            if result == 0:
                reply_msg = "【{0}】押了 {1} 分给{2}".format(user_nick, self.format_long_number(score), face)
            elif result == 1:
                return False
            elif result == 3:
                reply_msg = "【{0}】下 注 失败，积 分 不足".format(user_nick)
            else:
                reply_msg = "【{0}】下 注 失败，发生系统错误".format(user_nick)
            self.reply(reply_msg)
            return True
        else:
            return False
    def gamble_sx_end(self, face, result):
        reply_msg = "十二生肖结束了，本局 开 奖 为：\n    大码：{0}\n    小码：{1}".format("、".join(["%d"%n for n in face[0]]), "、".join(["%d"%n for n in face[1]]))
        for item in result:
            user_nick = self.game_helper.getItemFromListByProperty(self.user_nicks, 'id', item['user_id'])
            if user_nick: 
                user_nick = user_nick['nick']
                if item['earning'] > 0:
                    reply_msg += "\n[Cheers]【{0}】赢得了 {1} 积 分".format(user_nick, self.format_long_number(item['earning']))
                elif item['earning'] < 0:
                    reply_msg += "\n[BlowUp]【{0}】输掉了 {1} 积 分".format(user_nick, self.format_long_number(-item['earning']))
                else:
                    reply_msg += "\n[Lolly]【{0}】押得四平八稳，没赔也没赚。".format(user_nick)
        self.reply(reply_msg)

    def gamble_ggl(self, msg):
        msg_content = str(msg.content).strip(' ')
        reply_msg = None
        user_qq = self.get_user_qq(msg)
        user_nick = self.get_user_nick(msg)
        if msg_content == "刮刮乐":
            if (user_qq is None) or (user_nick is None):
                self.reply(self.error_msg)
                return True
            result = self.game_helper.gambleGgl(user_qq = user_qq)
            game_config = self.game_config.gambles.ggl
            reply_msg = "【{0}】".format(user_nick)
            if result >= 0 and result < len(game_config.prizes):
                prize_item = game_config.prizes[result]
                reply_msg += "花了 {0} 分参与幸运刮刮乐，获得{1}, 赢得了 {2} 分！".format(self.format_long_number(game_config.cost), prize_item.name, self.format_long_number(prize_item.score))
            elif result == -1:
                reply_msg += "没有足够的 积 分 参与 幸运刮刮乐"
            else:
                reply_msg += "参与刮刮乐失败，发生系统错误"
            self.reply(reply_msg)
            return True
        else:
            return False

    def admin(self, msg):
        msg_content = str(msg.content).strip(' ')
        reply_msg = None
        reg_exp = '(\d+)(充值|办理)(.+)'
        match = re.compile(reg_exp).match(msg_content)
        if match is None: return False
        administrator_qq = self.get_user_qq(msg)
        if (not self.__operator.sys_paras['debug']) and (not administrator_qq[2] in self.game_config.default.admin_qq):
            return False
        administrator_nick = self.get_user_nick(msg)
        user_qq = (administrator_qq[0], administrator_qq[1], match.group(1))
        if (administrator_qq is None) or (administrator_nick is None) or (user_qq is None):
            self.reply(self.error_msg)
            return True
        if match.group(2) == "充值":
            face = match.group(3)
            result = self.game_helper.adminCharge(face, user_qq = user_qq, administrator_qq = administrator_qq)
            if result == 0:
                score_gotten = self.game_helper.getCharge(face).score
                reply_msg = "【{0}】成功充(*￣3￣*)值{1}，获得 {2} 积 分".format(user_qq[2], face, self.format_long_number(score_gotten))
            elif result == 1:
                reply_msg = "【{0}】充(/TДT)/值失败，金 额 不合法。可充(*￣3￣*)值的 金 额 有：{1}".format(user_qq[2], "、".join(item.face for item in self.game_config.charges))
            elif result == 2:
                reply_msg = "充(/TДT)/值失败，【{0}】尚未在本群 注 册".format(user_qq[2])
            else:
                reply_msg = "充(/TДT)/值失败，发生系统错误。"
            self.reply(reply_msg)
            return True
        elif match.group(2) == "办理":
            face = match.group(3)
            result = self.game_helper.adminChargeMonthcard(face, user_qq = user_qq, administrator_qq = administrator_qq)
            monthcard_item = self.game_helper.getMonthcard(face)
            if isinstance(result, datetime.date):
                reply_msg = "【{0}】成功办(*￣3￣*)理{1}，{1}有效期至{2}".format(user_qq[2], face, (result + datetime.timedelta(-1)).strftime("%Y年%m月%d日"))
            elif result == 2:
                reply_msg = "办(/TДT)/理失败，【{0}】尚未在本群 注 册".format(user_qq[2])
            else:
                reply_msg = "办(/TДT)/理失败，发生系统错误。"
            self.reply(reply_msg)
            return True
        else:
            return False





