from GameConfigs import *

import MySQLdb
import time, datetime
import random

class Game:
    def __init__(self, long_connect = False):
        self.game_config = GameConfig().conf
        self.long_connect = True if long_connect else False
        self.conn_retain_count = 0
        if self.long_connect: self.connect()

    def __del__(self):
        # try:
        #     self.close()
        # except Exception, e:
        #     print "[Waring] failed to close game database connection"
        if self.long_connect: self.close()

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

    def timestamp(self):
        return int(time.time() * 1000)
    def datetime(self, timestamp = None):
        if timestamp is None:
            return datetime.datetime.now()
        else:
            return datetime.datetime.fromtimestamp(timestamp/1000)

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
            if rand == 0: return 0
            elif rand == 1: return len(rates) - 1
            for r in rates: total_rate += r
            for r in rates:
                if r == total_rate: break
                rate_sum += r / total_rate
                if rand < rate_sum: break
                idx += 1
            return idx
        elif isinstance(rates, dict):
            key_list = rates.keys
            if len(key_list) == 0: return None
            total_rate = 0
            rate_sum = 0
            rand = random.random()
            if rand == 0: return key_list[0]
            elif rand == 1: return key_list[-1]
            for k,r in rates.iteritem(): total_rate += r
            for k,r in rates.iteritem():
                if r == total_rate: return k
                rate_sum += r / total_rate
                if rand < rate_sum: return k
            return None

    def getUser(self, user_id = None, user_qq = None, no_insert = False):
        if not self.long_connect: self.connect()
        user = None
        if not user_id is None:
            if self.cur.execute('SELECT id, admin_qq, group_code, qq, score FROM user WHERE id = {0}'.format(user_id)):
                item = self.cur.fetchone()
                user = GameUser(_id = item[0], admin_qq = item[1], group_code = item[2], qq = item[3], score = item[4])
        elif self.is_valid_user_qq(user_qq):
            if self.cur.execute('SELECT id, admin_qq, group_code, qq, score FROM user WHERE admin_qq = "{0}" AND group_code = "{1}" AND qq = "{2}"'.format(user_qq[0], user_qq[1], user_qq[2])):
                item = self.cur.fetchone()
                user = GameUser(_id = item[0], admin_qq = item[1], group_code = item[2], qq = item[3], score = item[4])
            else:
                if self.cur.execute('INSERT INTO user (admin_qq, group_code, qq, score) VALUES ("{0}", "{1}", "{2}", {3})'.format(user_qq[0], user_qq[1], user_qq[2], self.game_config.default.score)) and not no_insert:
                    user = self.getUser(user_qq = user_qq, no_insert = True)
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

    def setUserScore(self, score, user_id = None, user_qq = None):
        if not self.long_connect: self.connect()
        user = self.getUser(user_id = user_id, user_qq = user_qq)
        if not user:
            if not self.long_connect: self.close()
            return False
        if user.score == score:
            if not self.long_connect: self.close()
            return True
        if not self.cur.execute('UPDATE user SET score = {0} WHERE id = {1}'.format(int(score), user.id)):
            if not self.long_connect: self.close()
            return False
        if not self.long_connect: self.close(True)
        return True

    def addUserScore(self, score, user_id = None, user_qq = None):
        if not self.long_connect: self.connect()
        user = self.getUser(user_id, user_qq)
        if not user: 
            if not self.long_connect: self.close()
            return False
        score = score + user.score
        if score < 0: 
            if not self.long_connect: self.close()
            return False
        self.setUserScore(int(score), user.id)
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

    def pay(self, user_id, pay_type, pay_id, pay_time = None):
        if not self.long_connect: self.connect()
        if self.cur.execute("SELECT earning FROM {0} WHERE id = {1}".format(pay_type, pay_id)):
            payment_record = self.cur.fetchone()
            payment_earning = payment_record[0]
            if payment_earning is None:
                if not self.long_connect: self.close(False)
                return False
            if not isinstance(pay_time, int): pay_time = self.timestamp()
            if self.cur.execute('INSERT INTO payment (user_id, ex_type, ex_id, value, time) VALUES ({0}, "{1}", {2}, {3}, {4})'.format(user_id, pay_type, pay_id, payment_earning, pay_time)):
                if not self.addUserScore(payment_earning, user_id):
                    if not self.long_connect: self.close(False)
                    return False
            else:
                if not self.long_connect: self.close(False)
                return False
        else:
            if not self.long_connect: self.close(False)
            return False
        if not self.long_connect: self.close(True)
        return True

    def dailySignin(self, user_id = None, user_qq = None):
        """
        0: success
        1: system error
        2: already have
        3: score negative
        """
        if not self.long_connect: self.connect()
        pet = self.getPet(user_id = user_id, user_qq = user_qq)
        if not pet: 
            if not self.long_connect: self.close(False)
            return 1
        if not self.setPetPower(self.game_config.default.power, pet.id):
            if not self.long_connect: self.close(False)
            return 1
        user = pet.user
        now_timestamp = self.timestamp()
        if self.cur.execute("SELECT time FROM sign_in ORDER BY time DESC LIMIT 1"):
            signin_record = self.cur.fetchone()
            last_signin_time = signin_record[0]
            if self.datetime(last_signin_time).date() == self.datetime(now_timestamp).date():
                if not self.long_connect: self.close(False)
                return 2
        score_to_add = self.game_config.default.signin_score
        if user.score + score_to_add < 0:
            if not self.long_connect: self.close()
            return 3
        if self.cur.execute("INSERT INTO sign_in (user_id, earning, time) VALUES ({0}, {1}, {2})".format(user.id, score_to_add, now_timestamp)):
            if self.cur.execute("SELECT id FROM sign_in ORDER BY time DESC LIMIT 1"):
                signin_record = self.cur.fetchone()
                signin_id = signin_record[0]
                if not self.pay(user.id, 'sign_in', signin_id, now_timestamp):
                    if not self.long_connect: self.close(False)
                    return 1
            else:
                if not self.long_connect: self.close(False)
                return 1
        else:
            if not self.long_connect: self.close(False)
            return 1
        if not self.long_connect: self.close(True)
        return 0

    def petPractice(self, pet):
        """
        1: insufficient pet power
        2: system error
        list: pay amount for each rule
        """
        if not isinstance(pet, GamePet):
            return 2
        if not self.long_connect: self.connect()
        practice_rules = self.game_config.levels[pet.level].practices
        practiceStatusList = []
        total_add_score = 0
        if not self.addPetPower(-self.game_config.default.power_cost_of_practice, pet.id):
            if not self.long_connect: self.close(False)
            return 1
        for rule in practice_rules:
            add_score = 0
            if self.random_judge(rule.rate):
                if abs(rule.score) > 1: add_score = int(rule.score)
                elif rule.score != 0: 
                    where_clause = ""
                    if rule.condition == "lose":
                        where_clause = 'ex_type = "gamble" AND value < 0'
                    if self.cur.execute("SELECT SUM(value) FROM payment WHERE " + where_clause):
                        add_score = int(abs(int(self.cur.fetchone()[0])) * rule.score)
                total_add_score += add_score
            practiceStatusList.append(add_score)
        if total_add_score != 0:
            pay_time = self.timestamp()
            if self.cur.execute("INSERT INTO practice (pet_id, earning, time) VALUES ({0}, {1}, {2})".format(pet.id, total_add_score, pay_time)):
                if self.cur.execute("SELECT id FROM practice WHERE pet_id = {0} ORDER BY time DESC LIMIT 1".format(pet.id)) and self.pay(pet.user.id, "practice", self.cur.fetchone().id, pay_time):
                    pass
                else:
                    if not self.long_connect: self.close(False)
                    return 2
            else:
                if not self.long_connect: self.close(False)
                return 2
        if not self.long_connect: self.close(True)
        return practiceStatusList

    def petLevelUp(self, pet):
        """
        0: success
        1: insufficient score
        2: highest level
        3: system error
        """
        if not isinstance(pet, GamePet):
            return 3
        if not pet.level + 1 < len(self.game_config.levels):
            return 2
        if not self.long_connect: self.connect()
        to_level = pet.level + 1
        score_cost = self.game_config.levels[to_level].score
        pay_time = self.timestamp()
        if not self.cur.execute("INSERT INTO level_up (pet_id, from_level, to_level, earning, time) VALUES ({0}, {1}, {2}, {3}, {4})".format(pet.id, pet.level, to_level, -score_cost, pay_time)):
            if not self.long_connect: self.close(False)
            return 3
        if self.cur.execute("SELECT id FROM level_up ORDER BY time DESC LIMIT 1"):
            if not self.pay(pet.user.id, 'level_up', self.cur.fetchone()[0], pay_time):
                if not self.long_connect: self.close(False)
                return 1
        else:
            if not self.long_connect: self.close(False)
            return 3
        if not self.cur.execute("UPDATE pet SET level = {0} WHERE id = {1}".format(to_level, pet.id)):
            if not self.long_connect: self.close(False)
            return 3
        if not self.long_connect: self.close(True)
        return 0

    def petWork(self, pet):
        if not isinstance(pet, GamePet):
            return 3
        score_earn = self.game_config.levels[pet.level]

class GameUser:
    def __init__(self,
            _id = -1,
            qq = "",
            admin_qq = "",
            group_code = "",
            score = 0):
        self.id = _id
        self.qq = qq
        self.admin_qq = admin_qq
        self.group_code = group_code
        self.score = score

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