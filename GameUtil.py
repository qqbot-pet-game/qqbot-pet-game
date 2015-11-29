from GameConfigs import *

import MySQLdb
import time, datetime, moment
import random
import threading
import copy
import logging

logging.basicConfig(
    filename='smartqq.log',
    level=logging.DEBUG,
    format='%(asctime)s  %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S',
)

class Game:
    def __init__(self, group_manager, long_connect = False, config_path = None):
        self.group_manager = group_manager
        self.config_path = config_path
        self.long_connect = True if long_connect else False
        self.conn_retain_count = 0
        self.update_config()
        self.current_gamble = None # should be a tuple: (str:type, int:id, prize_face, time_start)
        if self.long_connect: self.connect()

    def __del__(self):
        # try:
        #     self.close()
        # except Exception, e:
        #     print "[Waring] failed to close game database connection"
        if self.long_connect: self.close(True)

    def update_config(self):
        try:
            self.game_config = GameConfig(self.config_path).conf
            if self.long_connect: 
                self.close(True)
                self.connect()
            return True
        except Exception:
            pass
        return False

    def connect(self):
        if self.conn_retain_count == 0:
            self.conn = MySQLdb.connect(
                host = self.game_config.database.host,
                port = self.game_config.database.port,
                user = self.game_config.database.user,
                passwd = self.game_config.database.passwd,
                db = self.game_config.database.db)
            self.cur = self.conn.cursor()
        self.conn_retain_count += 1

    def close(self, commit = True):
        if not self.conn_retain_count > 1:
            self.cur.close()
            if commit: self.conn.commit()
            self.conn.close()
        self.conn_retain_count -= 1

    def startTransaction(self):
        if not self.long_connect:
            try:
                self.connect()
            except Exception, e:
                return False
            return True
        else:
            return False

    def endTransaction(self, accept):
        if not self.long_connect:
            try:
                commit = True if accept else False
                self.close(commit)
            except Exception, e:
                return False
            return True
        else:
            return False

    def forceClose(self, accept = False):
        if not self.long_connect:
            select.conn_retain_count = 0
        self.cur.close()
        if accept: self.conn.commit()
        self.conn.close()

    def wait(self, wait_time, callback, *callback_args):
        time.sleep(wait_time)
        callback(*callback_args)

    def timestamp(self, dt = None):
        if dt is None:
            return int(time.time() * 1000)
        else:
            return int(time.mktime((dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, 0, 0, 0)) * 1000)
    def datetime(self, timestamp = None):
        if timestamp is None:
            return datetime.datetime.now()
        else:
            return datetime.datetime.fromtimestamp(timestamp/1000)

    def getItemFromListByProperty(self, arr, prop, val):
        assert isinstance(arr, list), "arr must be a list"
        for item in arr:
            if isinstance(item, dict) and prop in item and item[prop] == val: return item
            elif hasattr(item, prop) and getattr(item, prop) == val: return item
        return None
    def sortListByProperty(self, arr, prop, reverse = False):
        assert isinstance(arr, list), "arr must be a list"
        def key(item):
            if isinstance(item, dict): return item[prop]
            else: return getattr(item, prop)
        return sorted(arr, key = key, reverse = reverse)
    def getCharge(self, face):
        return self.getItemFromListByProperty(self.game_config.charges, 'face', face)
    def getMonthcard(self, face):
        return self.getItemFromListByProperty(self.game_config.monthcards, 'face', face)

    def is_valid_user_qq(self, user_qq):
        return (not user_qq is None) and isinstance(user_qq, tuple) and (len(user_qq) == 3)

    def random_judge(self, rate):
        if rate == 0: return False
        elif rate == 1: return True
        else:
            if random.random() < rate:
                return True
    def random_select(self, rates):
        if isinstance(rates, list):
            if len(rates) == 0: return -1
            idx = 0
            total_rate = 0
            rate_sum = 0
            rand = random.random()
            # if rand == 0: return 0
            # elif rand == 1: return len(rates) - 1
            for r in rates: total_rate += r
            total_rate = float(total_rate)
            for r in rates:
                if r == total_rate: break
                rate_sum += r / total_rate
                if rand < rate_sum: break
                elif (rate_sum == 1) and (rand == 1): break
                idx += 1
            return idx
        elif isinstance(rates, dict):
            key_list = rates.keys()
            if len(key_list) == 0: return None
            total_rate = 0
            rate_sum = 0
            rand = random.random()
            # if rand == 0: return key_list[0]
            # elif rand == 1: return key_list[-1]
            for k,r in rates.items(): total_rate += r
            total_rate = float(total_rate)
            for k,r in rates.items():
                if r == total_rate: return k
                rate_sum += r / total_rate
                if rand < rate_sum: return k
                elif (rate_sum == 1) and (rand == 1): return k
            return None

    def random_select_multi(self, rates, cnt):
        idx_list = []
        rates = copy.copy(rates)
        if isinstance(rates, list):
            if len(rates) < cnt: return None
            while len(idx_list) < cnt:
                idx = self.random_select(rates)
                if idx is None: return None
                idx_list.append(idx)
                rates[idx] = 0
        elif isinstance(rates, dict):
            key_list = rates.keys()
            if len(key_list) < cnt: return None
            while len(idx_list) < cnt:
                idx = self.random_select(rates)
                if idx is None: return None
                idx_list.append(idx)
                rates[idx] = 0
        if len(idx_list) != cnt: return None
        else: return idx_list

    def getUser(self, user_id = None, user_qq = None, no_insert = False, count_frozen_score = True):
        if not self.long_connect: self.connect()
        user = None
        if not user_id is None:
            if self.cur.execute('SELECT id, admin_qq, group_nid, qq, score FROM user WHERE id = {0}'.format(user_id)):
                item = self.cur.fetchone()
                user = GameUser(_id = item[0], admin_qq = item[1], group_nid = item[2], qq = item[3], score = item[4])
        elif self.is_valid_user_qq(user_qq):
            if self.cur.execute('SELECT id, admin_qq, group_nid, qq, score FROM user WHERE group_nid = "{0}" AND qq = "{1}"'.format(user_qq[1], user_qq[2])):
                item = self.cur.fetchone()
                user = GameUser(_id = item[0], admin_qq = item[1], group_nid = item[2], qq = item[3], score = item[4])
            else:
                if self.cur.execute('INSERT INTO user (admin_qq, group_nid, qq, score) VALUES ("{0}", "{1}", "{2}", {3})'.format(user_qq[0], user_qq[1], user_qq[2], self.game_config.default.score)) and not no_insert:
                    user = self.getUser(user_qq = user_qq, no_insert = True)
        if not user is None:
            frozen_score = self.getUserFrozenScore(user.id)
            user.score = user.score - frozen_score
            user.frozenScore = frozen_score
        if not self.long_connect: self.close(True)
        return user

    def getPet(self, pet_id = None, user_id = None, user_qq = None, no_insert = False):
        if not self.long_connect: self.connect()
        pet = None
        if not pet_id is None:
            if self.cur.execute('SELECT id, user_id, level, power FROM pet WHERE id = {0}'.format(pet_id)):
                item = self.cur.fetchone()
                user = self.getUser(item[1])
                if user:
                    pet = GamePet(_id = item[0], user = user, level = item[2], power = item[3])
        else:
            user = None
            if not user_id is None:
                user = self.getUser(user_id = user_id)
            elif self.is_valid_user_qq(user_qq):
                user = self.getUser(user_qq = user_qq)
            if user:
                if self.cur.execute('SELECT id, user_id, level, power FROM pet WHERE user_id = {0}'.format(user.id)):
                    item = self.cur.fetchone()
                    pet = GamePet(_id = item[0], user = user, level = item[2], power = item[3])
                elif self.cur.execute('INSERT INTO pet (user_id, level, power) VALUES ({0}, {1}, {2})'.format(user.id, 0, self.game_config.default.power)) and not no_insert:
                    pet = self.getPet(user_id = user.id, no_insert = True)
        if not self.long_connect: self.close(True)
        return pet

    def getUserFrozenScore(self, user_id):
        if not self.long_connect: self.connect()
        frozen_score = 0
        # frozen in gambles: fqzs and sx
        if self.current_gamble and (self.current_gamble[0] in ["fqzs", "sx"]):
            self.cur.execute('SELECT SUM(cost) FROM gamble_{0} WHERE game_id = {1} AND user_id = {2}'.format(self.current_gamble[0], self.current_gamble[1], user_id))
            record = self.cur.fetchone()
            if record[0]:
                frozen_score += record[0]
        if not self.long_connect: self.close()
        return frozen_score


    def setUserScore(self, score, user_id = None, user_qq = None):
        if not self.long_connect: self.connect()
        user = self.getUser(user_id = user_id, user_qq = user_qq)
        if not user:
            if not self.long_connect: self.close()
            return False
        if user.totalScore() == score :
            if not self.long_connect: self.close()
            return True
        if not self.cur.execute('UPDATE user SET score = {0} WHERE id = {1}'.format(int(score), user.id)):
            if not self.long_connect: self.close()
            return False
        if not self.long_connect: self.close(True)
        return True

    def addUserScore(self, score, user_id = None, user_qq = None):
        if not self.long_connect: self.connect()
        # user = self.getUser(user_id, user_qq, count_frozen_score = False)
        user = self.getUser(user_id, user_qq, count_frozen_score = True)
        if not user: 
            if not self.long_connect: self.close()
            return False
        score = score + user.totalScore()
        if score < 0:
            if not self.long_connect: self.close()
            return False
        self.setUserScore(score - (user.frozenScore if False else 0), user.id)
        if not self.long_connect: self.close(True)
        return True

    def setPetPower(self, power, pet_id):
        if not self.long_connect: self.connect()
        pet = self.getPet(pet_id)
        if not pet:
            if not self.long_connect: self.close()
            return False
        if pet.power == power:
            if not self.long_connect: self.close()
            return True
        if not self.cur.execute('UPDATE pet SET power = {0} WHERE id = {1}'.format(int(power), pet_id)):
            if not self.long_connect: self.close()
            return False
        if not self.long_connect: self.close(True)
        return True

    def addPetPower(self, power, pet_id):
        if not self.long_connect: self.connect()
        pet = self.getPet(pet_id)
        if not pet: 
            if not self.long_connect: self.close()
            return False
        power = power + pet.power
        if power < 0: 
            if not self.long_connect: self.close()
            return False
        self.setPetPower(int(power), pet.id)
        if not self.long_connect: self.close(True)
        return True

    def pay(self, user_id, pay_type, pay_id, pay_score = 'earning', pay_time = 'time'):
        if not self.long_connect: self.connect()
        payment_earning = None
        payment_time = None
        select_fields = []
        if isinstance(pay_score, str): select_fields.append(pay_score)
        elif isinstance(pay_score, int): payment_earning = pay_score
        if isinstance(pay_time, str): select_fields.append(pay_time)
        elif isinstance(pay_time, int): payment_time = pay_time
        if select_fields and self.cur.execute("SELECT {0} FROM {1} WHERE id = {2}".format(",".join(select_fields), pay_type, pay_id)):
            payment_record = self.cur.fetchone()
            if isinstance(pay_score, str): 
                payment_earning = payment_record[0]
                if isinstance(pay_time, str):
                    payment_time = payment_record[1]
            elif isinstance(pay_time, str):
                payment_time = payment_record[0]
        if (payment_earning is None) or (payment_time is None):
            if not self.long_connect: self.close(False)
            return False
        if not isinstance(payment_time, int): payment_time = self.timestamp()
        if self.cur.execute('INSERT INTO payment (user_id, ex_type, ex_id, value, time) VALUES ({0}, "{1}", {2}, {3}, {4})'.format(user_id, pay_type, pay_id, payment_earning, payment_time)):
            if not self.addUserScore(int(payment_earning), user_id):
                if not self.long_connect: self.close(False)
                return False
        else:
            if not self.long_connect: self.close(False)
            return False
        if not self.long_connect: self.close(True)
        return True

    def dailySignin(self, user_id = None, user_qq = None, monthcard_face = None):
        """
        0: success
        2: already have
        3: score negative
        4: monthcard face not valid
        5: no monthcard registered / monthcard overdue
        100: system error
        """
        monthcard_item = self.getMonthcard(monthcard_face)
        if not monthcard_item and monthcard_face:
            return 4
        if not self.long_connect: self.connect()
        pet = self.getPet(user_id = user_id, user_qq = user_qq)
        if not pet: 
            logging.warning("<detected error> pet not found")
            if not self.long_connect: self.close(False)
            return 100
        if not self.setPetPower(self.game_config.default.power, pet.id):
            logging.warning("<detected error> pet power reset failed")
            if not self.long_connect: self.close(False)
            return 100
        user = pet.user
        now_timestamp = self.timestamp()
        monthcard_id = None
        score_to_add = self.game_config.default.signin_score
        if user.score + score_to_add < 0:
            if not self.long_connect: self.close()
            return 3
        if self.cur.execute("SELECT time FROM sign_in WHERE user_id = {0} ORDER BY time DESC LIMIT 1".format(user.id)):
            signin_record = self.cur.fetchone()
            last_signin_time = signin_record[0]
            if self.datetime(last_signin_time).date() == self.datetime(now_timestamp).date():
                if not self.long_connect: self.close(False)
                return 2
        if monthcard_item:
            if self.cur.execute('SELECT id FROM monthcard WHERE user_id = {0} AND face = "{1}" AND time_start <= {2} AND time_end > {2} ORDER BY time_end ASC LIMIT 1'.format(user.id, monthcard_item.face, now_timestamp)):
                monthcard_id = self.cur.fetchone()[0]
                score_to_add = monthcard_item.score
            else:
                if not self.long_connect: self.close(False)
                return 5
        if self.cur.execute("INSERT INTO sign_in (user_id, monthcard, earning, time) VALUES ({0}, {1}, {2}, {3})".format(user.id, 'NULL' if monthcard_id is None else monthcard_id, score_to_add, now_timestamp)):
            if self.cur.execute("SELECT id FROM sign_in WHERE user_id = {0} AND time = {1}".format(user.id, now_timestamp)):
                signin_record = self.cur.fetchone()
                signin_id = signin_record[0]
                if not self.pay(user.id, 'sign_in', signin_id, 'earning', 'time'):
                    logging.warning("<detected error> add user score failed")
                    if not self.long_connect: self.close(False)
                    return 100
            else:
                logging.warning("<detected error> cannot find the user")
                if not self.long_connect: self.close(False)
                return 100
        else:
            logging.warning("<detected error> insert sign_in record failed")
            if not self.long_connect: self.close(False)
            return 100
        if not self.long_connect: self.close(True)
        return 0

    def petPractice(self, pet):
        """
        1: insufficient pet power
        100: system error
        list: pay amount for each rule
        """
        if not isinstance(pet, GamePet):
            logging.warning("<detected error> pet is not instance of GamePet")
            return 100
        if not self.long_connect: self.connect()
        practice_rules = self.game_config.levels[pet.level].practices
        practiceStatusList = []
        total_add_score = 0
        if pet.power < self.game_config.default.power_cost_of_practice:
            if not self.long_connect: self.close(False)
            return 1
        if not self.addPetPower(-self.game_config.default.power_cost_of_practice, pet.id):
            logging.warning("<detected error> deduct pet power failed")
            if not self.long_connect: self.close(False)
            return 100
        for rule in practice_rules:
            add_score = 0
            if self.random_judge(rule.rate):
                if abs(rule.score) > 1: add_score = int(rule.score)
                elif rule.score != 0: 
                    where_clause = "user_id = {0}".format(pet.user.id)
                    value_clause = "SUM(value)"
                    if rule.condition == "lose":
                        today = self.datetime()
                        where_clause += ' AND ex_type = "gamble" AND time > {0} AND value < 0'.format(self.timestamp(moment.date(today.year, today.month, today.day).date))
                    if self.cur.execute('SELECT {0} FROM payment WHERE {1}'.format(value_clause, where_clause)):
                        sum_value = self.cur.fetchone()[0]
                        if sum_value:
                            fetch_value = int(sum_value)
                            if rule.condition == "lose":
                                if fetch_value < 0: add_score = int(-fetch_value * rule.score)
                            else:
                                add_score = int(abs(fetch_value) * rule.score)
                    else:
                        logging.warning("<detected error> cannot find the payment")
                        if not self.long_connect: self.close(False)
                        return 100
            total_add_score += add_score
            practiceStatusList.append(add_score)
        if total_add_score != 0:
            pay_time = self.timestamp()
            if self.cur.execute("INSERT INTO practice (pet_id, earning, time) VALUES ({0}, {1}, {2})".format(pet.id, total_add_score, pay_time)):
                if self.cur.execute("SELECT id FROM practice WHERE pet_id = {0} AND time = {1}".format(pet.id, pay_time)) \
                        and self.pay(pet.user.id, "practice", self.cur.fetchone()[0], 'earning', 'time'):
                    pass
                else:
                    logging.warning("<detected error> query practice record failed")
                    if not self.long_connect: self.close(False)
                    return 100
            else:
                logging.warning("<detected error> insert practice record failed")
                if not self.long_connect: self.close(False)
                return 100
        if not self.long_connect: self.close(True)
        return practiceStatusList

    def petLevelUp(self, pet):
        """
        0: success
        1: insufficient score
        2: highest level
        100: system error
        """
        if not isinstance(pet, GamePet):
            logging.warning("<detected error> pet is not instance of GamePet")
            return 100
        if not pet.level + 1 < len(self.game_config.levels):
            return 2
        if not self.long_connect: self.connect()
        to_level = pet.level + 1
        score_cost = self.game_config.levels[to_level].score
        pay_time = self.timestamp()
        if not self.cur.execute("INSERT INTO level_up (pet_id, from_level, to_level, cost, time) VALUES ({0}, {1}, {2}, {3}, {4})".format(pet.id, pet.level, to_level, score_cost, pay_time)):
            logging.warning("<detected error> insert level_up record failed")
            if not self.long_connect: self.close(False)
            return 100
        if self.cur.execute("SELECT id FROM level_up WHERE pet_id = {0} AND time = {1}".format(pet.id, pay_time)):
            if not self.pay(pet.user.id, 'level_up', self.cur.fetchone()[0], '-cost', 'time'):
                if not self.long_connect: self.close(False)
                return 1
        else:
            logging.warning("<detected error> query level_up record failed")
            if not self.long_connect: self.close(False)
            return 100
        if not self.cur.execute("UPDATE pet SET level = {0} WHERE id = {1}".format(to_level, pet.id)):
            logging.warning("<detected error> update pet level failed")
            if not self.long_connect: self.close(False)
            return 100
        if not self.long_connect: self.close(True)
        return 0

    def petWorkStart(self, pet):
        """
        0: success
        1: in work
        2: no ability
        100: system error
        """
        if not isinstance(pet, GamePet):
            logging.warning("<detected error> pet is not instance of GamePet")
            return 100
        score_earn = self.game_config.levels[pet.level].earning
        if score_earn <= 0:
            return 2
        if not self.long_connect: self.connect()
        now_timestamp = self.timestamp()
        work_interval = self.game_config.default.work_interval * 1000
        if self.cur.execute("SELECT id FROM work WHERE pet_id = {0} AND time_end = 0 ORDER BY time_start DESC LIMIT 1".format(pet.id)):
            if not self.long_connect: self.close(False)
            return 1
        if not self.cur.execute("INSERT INTO work (pet_id, time_start, time_end, earning) VALUES ({0}, {1}, {2}, {3})".format(pet.id, now_timestamp, 0, score_earn)):
            logging.warning("<detected error> insert work record failed")
            if not self.long_connect: self.close(False)
            return 100
        if not self.long_connect: self.close(True)
        return 0

    def petWorkEnd(self, pet):
        """
        0: success
        1: not in work
        2: time not satisfied
        2: pay failed
        100: system error
        """
        if not isinstance(pet, GamePet):
            logging.warning("<detected error> pet is not instance of GamePet")
            return 100
        if not self.long_connect: self.connect()
        now_timestamp = self.timestamp()
        work_interval = self.game_config.default.work_interval * 1000
        if self.cur.execute("SELECT id, time_start FROM work WHERE pet_id = {0} AND time_end = 0 ORDER BY time_start DESC LIMIT 1".format(pet.id)):
            record = self.cur.fetchone()
            record_id = record[0]
            record_time_start = record[1]
            if record_time_start > now_timestamp - work_interval:
                if not self.long_connect: self.close(False)
                return 2
            if not self.cur.execute("UPDATE work SET time_end = {0} WHERE id = {1}".format(now_timestamp, record_id)):
                logging.warning("<detected error> update work record failed")
                if not self.long_connect: self.close(False)
                return 100
            if not self.pay(pet.user.id, 'work', record_id, 'earning', 'time_end'):
                logging.warning("<detected error> add user score failed")
                if not self.long_connect: self.close(False)
                return 100
        else:
            if not self.long_connect: self.close(False)
            return 1
        if not self.long_connect: self.close(True)
        return 0

    def addGamble(self, gamble_type, gamble_id, pay_score = 'earning - cost', pay_time = 'time'):
        if not self.long_connect: self.connect()
        gamble_earning = None
        gamble_time = None
        select_fields = ['user_id']
        user_id = None
        if isinstance(pay_score, str): select_fields.append(pay_score)
        elif isinstance(pay_score, int): gamble_earning = pay_score
        if isinstance(pay_time, str): select_fields.append(pay_time)
        elif isinstance(pay_time, int): gamble_time = pay_time
        if select_fields and self.cur.execute("SELECT {0} FROM {1} WHERE id = {2}".format(",".join(select_fields), "gamble_" + gamble_type, gamble_id)):
            gamble_record = self.cur.fetchone()
            user_id = gamble_record[0]
            if isinstance(pay_score, str): 
                gamble_earning = gamble_record[1]
                if isinstance(pay_time, str):
                    gamble_time = gamble_record[2]
            elif isinstance(pay_time, str):
                gamble_time = gamble_record[1]
        if (gamble_earning is None) or (gamble_time is None) or (user_id is None):
            logging.warning("<detected error> query gamble info failed")
            if not self.long_connect: self.close(False)
            return False
        if not isinstance(gamble_time, int): gamble_time = self.timestamp()
        if self.cur.execute('INSERT INTO gamble (user_id, ex_type, ex_id, earning, time) VALUES ({0}, "{1}", {2}, {3}, {4})'.format(user_id, gamble_type, gamble_id, gamble_earning, gamble_time)) \
                and self.cur.execute('SELECT id, user_id FROM gamble WHERE ex_type = "{0}" and ex_id = {1}'.format(gamble_type, gamble_id)):
            gamble_record = self.cur.fetchone()
            if not self.pay(gamble_record[1], 'gamble', gamble_record[0], 'earning', 'time'):
                logging.warning("<detected error> pay failed")
                if not self.long_connect: self.close(False)
                return False
        else:
            logging.warning("<detected error> insert gamble record failed")
            if not self.long_connect: self.close(False)
            return False
        if not self.long_connect: self.close(True)
        return True

    def gambleFqzsStart(self, user_id = None, user_qq = None):
        """
        0: success
        1: in gamble
        100: system error
        """
        game_config = self.game_config.gambles.fqzs
        if (not self.current_gamble is None) and (self.timestamp() - self.current_gamble[3] < game_config.time * 1000):
            return 1
        if not self.long_connect: self.connect()
        user = self.getUser(user_id = user_id, user_qq = user_qq)
        if not user:
            logging.warning("<detected error> user not found")
            if not self.long_connect: self.close(False)
            return 100
        now_timestamp = self.timestamp()
        face_idx = self.random_select([item.rate for item in game_config.items])
        if face_idx < 0 or face_idx >= len(game_config.items):
            logging.warning("<detected error> random select out of range")
            if not self.long_connect: self.close(False)
            return 100
        face = game_config.items[face_idx].name
        if not self.cur.execute('INSERT INTO gamble_fqzs_game (user_id, time_start, time_end, face) VALUES ({0}, {1}, {2}, "{3}")'.format(user.id, now_timestamp, 0, face)):
            logging.warning("<detected error> insert gamble_fqzs_game record failed")
            if not self.long_connect: self.close(False)
            return 100
        if not self.cur.execute('SELECT id FROM gamble_fqzs_game WHERE time_start = {0}'.format(now_timestamp)):
            logging.warning("<detected error> query gamble_fqzs_game record failed")
            if not self.long_connect: self.close(False)
            return 100
        gamble_record = self.cur.fetchone()
        self.current_gamble = ('fqzs', gamble_record[0], str(face), now_timestamp)
        t = threading.Thread(target = self.wait, args = (game_config.time, self.gambleFqzsEnd))
        t.setDaemon(True)
        t.start()
        if not self.long_connect: self.close(True)
        return 0

    def gambleFqzsPour(self, face, pay_score, user_id = None, user_qq = None):
        """
        0: success
        1: not in gamble
        2: item not valid
        3: insufficient score
        100: system error
        """
        if self.current_gamble is None or self.current_gamble[0] != "fqzs":
            return 1
        game_config = self.game_config.gambles.fqzs
        face_item = self.getItemFromListByProperty(game_config.prizes, 'name', face)
        if not face_item:
            return 2
        if not self.long_connect: self.connect()
        user = self.getUser(user_id = user_id, user_qq = user_qq)
        if not user:
            logging.warning("<detected error> user not found")
            if not self.long_connect: self.close(False)
            return 100
        if user.score < pay_score:
            if not self.long_connect: self.close(False)
            return 3
        game_id = self.current_gamble[1]
        earning = 0
        if self.current_gamble[2] in [str(item) for item in face_item.items]:
            earning = pay_score * face_item.rate
        now_timestamp = self.timestamp()
        if not self.cur.execute('INSERT INTO gamble_fqzs (user_id, game_id, face, cost, earning, time_pay, time_earn) VALUES ({0}, {1}, "{2}", {3}, {4}, {5}, {6})'.format(user.id, game_id, face, pay_score, earning, now_timestamp, 0)):
            logging.warning("<detected error> insert gamble_fqzs record failed")
            if not self.long_connect: self.close(False)
            return 100
        if not self.long_connect: self.close(True)
        return 0

    def gambleFqzsEnd(self):
        """
        0: success
        1: not in gamble
        100: system error
        """
        if self.current_gamble is None:
            return 1
        if not self.long_connect: self.connect()
        game_id = self.current_gamble[1]
        now_timestamp = self.timestamp()
        game_config = self.game_config.gambles.fqzs
        if not self.cur.execute('UPDATE gamble_fqzs_game SET time_end = {0} WHERE id = {1}'.format(now_timestamp, game_id)):
            logging.warning("<detected error> update gamble_fqzs_game record failed")
            if not self.long_connect: self.close(False)
            return 100
        self.cur.execute('UPDATE gamble_fqzs SET time_earn = {0} WHERE game_id = {1}'.format(now_timestamp, game_id))
        self.cur.execute('SELECT id, user_id, face, cost, earning FROM gamble_fqzs WHERE game_id = {0}'.format(game_id))
        pour_records = []
        while True:
            record = self.cur.fetchone()
            if record is None: break
            pour_records.append({'id': record[0], 'user_id': record[1], 'face': record[2], 'cost': record[3], 'earning': record[4]})
        result = []
        for record in pour_records:
            if not self.addGamble('fqzs', record['id'], 'earning - cost', 'time_earn'):
                logging.warning("<detected error> add gamble failed")
                if not self.long_connect: self.close(False)
                return 100
            item = self.getItemFromListByProperty(result, 'user_id', record['user_id'])
            if item: item['earning'] += (record['earning'] - record['cost'])
            else: result.append({'user_id': record['user_id'], 'earning': record['earning'] - record['cost']})
        result = self.sortListByProperty(result, 'earning', reverse = True)
        face = self.current_gamble[2]
        self.current_gamble = None
        if not self.long_connect: self.close(True)
        self.group_manager.gamble_fqzs_end(face, result)
        return 0

    def gambleSxStart(self, user_id = None, user_qq = None):
        """
        0: success
        1: in gamble
        100: system error
        """
        game_config = self.game_config.gambles.sx
        if (not self.current_gamble is None) and (self.timestamp() - self.current_gamble[3] < game_config.time * 1000):
            return 1
        if not self.long_connect: self.connect()
        user = self.getUser(user_id = user_id, user_qq = user_qq)
        if not user:
            logging.warning("<detected error> user not found")
            if not self.long_connect: self.close(False)
            return 100
        now_timestamp = self.timestamp()
        number_idx_list = self.random_select_multi([item.rate for item in game_config.numbers], game_config.cnt_big + game_config.cnt_small)
        number_big = []
        number_small = []
        if number_idx_list is None:
            logging.warning("<detected error> random select failed")
            if not self.long_connect: self.close(False)
            return 100
        for number_idx in number_idx_list:
            if number_idx < 0 or number_idx >= len(game_config.numbers):
                logging.warning("<detected error> random select range out of range")
                if not self.long_connect: self.close(False)
                return 100
        number_big = [game_config.numbers[number_idx].number for number_idx in number_idx_list[0:game_config.cnt_big]]
        number_small = [game_config.numbers[number_idx].number for number_idx in number_idx_list[game_config.cnt_big:game_config.cnt_big+game_config.cnt_small]]
        if not self.cur.execute('INSERT INTO gamble_sx_game (user_id, time_start, time_end, number_big, number_small) VALUES ({0}, {1}, {2}, "{3}", "{4}")'.format(user.id, now_timestamp, 0, [" ".join(["%d"%n for n in number_big])], [" ".join(["%d"%n for n in number_small])])):
            logging.warning("<detected error> insert gamble_sx_game record failed")
            if not self.long_connect: self.close(False)
            return 100
        if not self.cur.execute('SELECT id FROM gamble_sx_game WHERE time_start = {0}'.format(now_timestamp)):
            logging.warning("<detected error> query gamble_sx_game record failed")
            if not self.long_connect: self.close(False)
            return 100
        gamble_record = self.cur.fetchone()
        self.current_gamble = ('sx', gamble_record[0], (number_big, number_small), now_timestamp)
        t = threading.Thread(target = self.wait, args = (game_config.time, self.gambleSxEnd))
        t.setDaemon(True)
        t.start()
        if not self.long_connect: self.close(True)
        return 0

    def gambleSxPour(self, face, pay_score, user_id = None, user_qq = None):
        """
        0: success
        1: not in gamble
        2: item not valid
        3: insufficient score
        100: system error
        """
        if self.current_gamble is None or self.current_gamble[0] != "sx":
            return 1
        game_config = self.game_config.gambles.sx
        face_item = self.getItemFromListByProperty(game_config.prizes, 'name', face)
        if not face_item:
            return 2
        if not self.long_connect: self.connect()
        user = self.getUser(user_id = user_id, user_qq = user_qq)
        if not user:
            logging.warning("<detected error> user not found")
            if not self.long_connect: self.close(False)
            return 100
        if user.score < pay_score:
            if not self.long_connect: self.close(False)
            return 3
        game_id = self.current_gamble[1]
        earning = 0
        for number in self.current_gamble[2][0]:
            if number in face_item.numbers:
                earning += pay_score * face_item.rate_big
        for number in self.current_gamble[2][1]:
            if number in face_item.numbers:
                earning += pay_score * face_item.rate_small
        now_timestamp = self.timestamp()
        if not self.cur.execute('INSERT INTO gamble_sx (user_id, game_id, face, cost, earning, time_pay, time_earn) VALUES ({0}, {1}, "{2}", {3}, {4}, {5}, {6})'.format(user.id, game_id, face, pay_score, earning, now_timestamp, 0)):
            logging.warning("<detected error> insert gamble_sx record failed")
            if not self.long_connect: self.close(False)
            return 100
        if not self.long_connect: self.close(True)
        return 0

    def gambleSxEnd(self):
        """
        0: success
        1: not in gamble
        100: system error
        """
        if self.current_gamble is None:
            return 1
        if not self.long_connect: self.connect()
        game_id = self.current_gamble[1]
        now_timestamp = self.timestamp()
        game_config = self.game_config.gambles.sx
        if not self.cur.execute('UPDATE gamble_sx_game SET time_end = {0} WHERE id = {1}'.format(now_timestamp, game_id)):
            logging.warning("<detected error> update gamble_sx_game failed")
            if not self.long_connect: self.close(False)
            return 100
        self.cur.execute('UPDATE gamble_sx SET time_earn = {0} WHERE game_id = {1}'.format(now_timestamp, game_id))
        self.cur.execute('SELECT id, user_id, face, cost, earning FROM gamble_sx WHERE game_id = {0}'.format(game_id))
        pour_records = []
        while True:
            record = self.cur.fetchone()
            if record is None: break
            pour_records.append({'id': record[0], 'user_id': record[1], 'face': record[2], 'cost': record[3], 'earning': record[4]})
        result = []
        for record in pour_records:
            if not self.addGamble('sx', record['id'], 'earning - cost', 'time_earn'):
                logging.warning("<detected error> add gamble failed")
                if not self.long_connect: self.close(False)
                return 100
            item = self.getItemFromListByProperty(result, 'user_id', record['user_id'])
            if item: item['earning'] += (record['earning'] - record['cost'])
            else: result.append({'user_id': record['user_id'], 'earning': record['earning'] - record['cost']})
        result = self.sortListByProperty(result, 'earning', reverse = True)
        number = self.current_gamble[2]
        self.current_gamble = None
        if not self.long_connect: self.close(True)
        self.group_manager.gamble_sx_end(number, result)
        return 0

    def gambleGgl(self, user_id = None, user_qq = None):
        """
        non-negative integer: prize index
        -1: not enough score
        -100: system error
        """
        if not self.long_connect: self.connect()
        user = self.getUser(user_id = user_id, user_qq = user_qq)
        if not user:
            logging.warning("<detected error> user not found")
            if not self.long_connect: self.close(False)
            return -100
        game_config = self.game_config.gambles.ggl
        if user.score < game_config.cost:
            if not self.long_connect: self.close(False)
            return -1
        prize_cnt = len(game_config.prizes)
        idx = self.random_select([item.rate for item in game_config.prizes])
        if idx < 0 or idx >= prize_cnt:
            logging.warning("<detected error> random select out of range")
            if not self.long_connect: self.close(False)
            return -100
        prize_item = game_config.prizes[idx]
        now_timestamp = self.timestamp()
        if self.cur.execute("INSERT INTO gamble_ggl (user_id, prize, cost, earning, time) VALUES ({0}, {1}, {2}, {3}, {4})".format(user.id, idx, game_config.cost, prize_item.score, now_timestamp)) \
                and self.cur.execute("SELECT id FROM gamble_ggl WHERE user_id = {0} AND time = {1}".format(user.id, now_timestamp)) \
                and self.addGamble('ggl', self.cur.fetchone()[0], 'earning - cost', 'time'):
            pass
        else:
            logging.warning("<detected error> insert gamble_ggl failed")
            if not self.long_connect: self.close(False)
            return -100
        if not self.long_connect: self.close(True)
        return idx

    def adminCharge(self, face, user_id = None, user_qq = None, administrator_id = None, administrator_qq = None):
        """
        0: success
        1: face not valid
        2: user not exist
        100: system error
        """
        charge_item = self.getCharge(face)
        if not charge_item:
            return 1
        if not self.long_connect: self.connect()
        user = self.getUser(user_id, user_qq, no_insert = True)
        administrator = self.getUser(administrator_id, administrator_qq)
        if not user: 
            if not self.long_connect: self.close(False)
            return 2
        if not administrator:
            logging.warning("<detected error> administrator not found")
            if not self.long_connect: self.close(False)
            return 100
        now_timestamp = self.timestamp()
        if not self.cur.execute('INSERT INTO charge (user_id, administrator_id, face, score, time) VALUES ({0}, {1}, "{2}", {3}, {4})'.format(user.id, administrator.id, face, charge_item.score, now_timestamp)) \
                or not self.cur.execute('SELECT id FROM charge WHERE user_id = {0} AND administrator_id = {1} AND time = {2}'.format(user.id, administrator.id, now_timestamp)) \
                or not self.pay(user.id, 'charge', self.cur.fetchone()[0], 'score', 'time'):
            logging.warning("<detected error> insert charge record failed")
            if not self.long_connect: self.close(False)
            return 100
        if not self.long_connect: self.close(True)
        return 0

    def adminChargeMonthcard(self, face, user_id = None, user_qq = None, administrator_id = None, administrator_qq = None):
        """
        date object: end date
        1: face not valid
        2: user not exist
        100: system error
        """
        card_item = self.getMonthcard(face)
        if not card_item:
            return 1
        if not self.long_connect: self.connect()
        user = self.getUser(user_id, user_qq, no_insert = True)
        administrator = self.getUser(administrator_id, administrator_qq)
        if not user: 
            if not self.long_connect: self.close(False)
            return 2
        if not administrator:
            logging.warning("<detected error> administrator not found")
            if not self.long_connect: self.close(False)
            return 100
        now_timestamp = self.timestamp()
        today = self.datetime(now_timestamp)
        today = moment.date(today.year, today.month, today.day).date
        start_timestamp = self.timestamp(today)
        if self.cur.execute('SELECT time_end FROM monthcard WHERE user_id = {0} AND face = "{1}" ORDER BY time_end DESC LIMIT 1'.format(user.id, face)):
            record = self.cur.fetchone()
            if record[0] > start_timestamp: start_timestamp = record[0]
        start_time = self.datetime(start_timestamp)
        start_time = moment.date(start_time.year, start_time.month, start_time.day)
        end_time = start_time.clone().add(months = 1).date
        start_time = start_time.date
        start_timestamp = self.timestamp(start_time)
        end_timestamp = self.timestamp(end_time)
        if not self.cur.execute('INSERT INTO monthcard (user_id, administrator_id, face, time_register, time_start, time_end) VALUES ({0}, {1}, "{2}", {3}, {4}, {5})'.format(user.id, administrator.id, face, now_timestamp, start_timestamp, end_timestamp)):
            logging.warning("<detected error> insert monthcard record not found")
            if not self.long_connect: self.close(False)
            return 100
        if not self.long_connect: self.close(True)
        return datetime.date.fromtimestamp(end_timestamp/1000)

class GameUser:
    def __init__(self,
            _id = -1,
            qq = "",
            admin_qq = "",
            group_nid = "",
            score = 0):
        self.id = _id
        self.qq = qq
        self.admin_qq = admin_qq
        self.group_nid = group_nid
        self.score = score
        self.frozenScore = 0
    def totalScore(self):
        return self.score + self.frozenScore

class GamePet:
    def __init__(self,
            _id = -1,
            user = None,
            level = 0,
            power = 0):
        self.id = _id
        self.user = user
        self.level = level
        self.power = power