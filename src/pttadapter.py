import datetime
import random
import string
import threading
import time

from PyPtt import PTT

from backend_util.src.log import Logger
from dialogue import Dialogue
from backend_util.src.errorcode import ErrorCode
from backend_util.src.msg import Msg
from backend_util.src.util import sha256


class PTT_Adapter:
    def __init__(self, console_obj):
        self.console = console_obj

        console_obj.event.login.append(self.event_login)
        console_obj.event.logout.append(self.event_logout)
        console_obj.event.close.append(self.event_logout)
        console_obj.event.close.append(self.event_close)
        console_obj.event.send_waterball.append(self.event_send_waterball)

        self.logger = Logger('PTTAdapter', Logger.INFO)

        self.dialogue = None

        self.bot = None
        self.ptt_id = None
        self.ptt_pw = None

        self.recv_logout = False

        self.run_server = True
        self.login = False

        self.has_new_mail = False
        self.res_msg = None

        self.send_waterball_list = []
        self.send_waterball_complete = True
        self.send_waterball = False

        self.init_bot()

        self.thread = threading.Thread(
            target=self.run,
            daemon=True
        )
        self.thread.start()
        time.sleep(0.5)

    def init_bot(self):
        self.ptt_id = None
        self.ptt_pw = None

        self.recv_logout = False

        self.login = False

        self.send_waterball_list = []

        self.has_new_mail = False

    def event_logout(self):
        self.recv_logout = True

    def event_close(self):
        self.logger.show(
            Logger.INFO,
            '執行終止程序')
        # self.logout()
        self.run_server = False
        self.thread.join()
        self.logger.show(
            Logger.INFO,
            '終止程序完成')

    def event_login(self, ptt_id, ptt_pw):

        self.ptt_id = ptt_id
        self.ptt_pw = ptt_pw

        while self.ptt_id is not None:
            time.sleep(self.console.config.quick_response_time)

        return self.res_msg

    def event_send_waterball(self, waterball_id, waterball_content):

        self.send_waterball_complete = False

        self.send_waterball_list.append(
            (waterball_id, waterball_content))

        self.send_waterball = True

        while not self.send_waterball_complete:
            time.sleep(self.console.config.quick_response_time)

    def run(self):

        self.logger.show(
            Logger.INFO,
            '啟動')

        self.bot = PTT.API(
            log_handler=self.console.config.ptt_log_handler,
            # log_level=self.console.config.ptt_log_level
            log_level=Logger.SILENT
        )
        while self.run_server:
            # 快速反應區
            start_time = end_time = time.time()
            while end_time - start_time < self.console.config.query_cycle:

                if not self.run_server:
                    break

                if (self.ptt_id, self.ptt_pw) != (None, None):
                    self.logger.show(
                        Logger.INFO,
                        '執行登入')
                    try:
                        self.bot.login(
                            self.ptt_id,
                            self.ptt_pw,
                            kick_other_login=True)

                        self.console.ptt_id = self.ptt_id

                        self.console.config.init_user(self.ptt_id)
                        self.dialogue = Dialogue(self.console)
                        self.console.dialogue = self.dialogue

                        self.login = True
                        self.bot.set_call_status(PTT.data_type.call_status.OFF)

                        self.res_msg = Msg(
                            operate=Msg.key_login,
                            code=ErrorCode.Success,
                            msg='Login success'
                        )

                        letters = string.ascii_lowercase
                        rand_str = ''.join(random.choice(letters) for i in range(256))

                        token = sha256(f'{self.ptt_id}{self.ptt_pw}{rand_str}')
                        self.console.login_token = token

                        payload = Msg()
                        payload.add(Msg.key_token, token)

                        self.res_msg.add(Msg.key_payload, payload)

                        self.logger.show(
                            Logger.INFO,
                            '執行登入成功程序')
                        for e in self.console.event.login_success:
                            e()
                        self.logger.show(
                            Logger.INFO,
                            '登入成功程序全數完成')

                    except PTT.exceptions.LoginError:
                        self.res_msg = Msg(
                            operate=Msg.key_login,
                            code=ErrorCode.LoginFail,
                            msg='Login fail'
                        )
                    except PTT.exceptions.WrongIDorPassword:
                        self.res_msg = Msg(
                            operate=Msg.key_login,
                            code=ErrorCode.LoginFail,
                            msg='ID or PW error'
                        )
                    except PTT.exceptions.LoginTooOften:
                        self.res_msg = Msg(
                            operate=Msg.key_login,
                            code=ErrorCode.LoginFail,
                            msg='Please wait a moment before login'
                        )
                    self.ptt_id = None
                    self.ptt_pw = None

                if self.login:

                    if self.recv_logout:
                        self.logger.show(
                            Logger.INFO,
                            '執行登出')

                        self.bot.logout()

                        res_msg = Msg(
                            operate=Msg.key_logout,
                            code=ErrorCode.Success,
                            msg='Logout success')

                        self.console.command.push(res_msg)

                        self.init_bot()

                    if self.send_waterball:

                        while self.send_waterball_list:
                            waterball_id, waterball_content = self.send_waterball_list.pop()

                            try:
                                self.logger.show(
                                    Logger.INFO,
                                    '準備丟水球')
                                self.bot.throw_waterball(waterball_id, waterball_content)
                                self.logger.show(
                                    Logger.INFO,
                                    '丟水球完畢，準備儲存')

                                current_dialogue_msg = Msg()
                                current_dialogue_msg.add(Msg.key_ptt_id, waterball_id)
                                current_dialogue_msg.add(Msg.key_content, waterball_content)
                                current_dialogue_msg.add(Msg.key_msg_type, 'send')

                                timestamp = int(datetime.datetime.now().timestamp())
                                current_dialogue_msg.add(Msg.key_timestamp, timestamp)

                                self.dialogue.save(current_dialogue_msg)

                                res_msg = Msg(
                                    operate=Msg.key_sendwaterball,
                                    code=ErrorCode.Success,
                                    msg='send waterball success')
                            except PTT.exceptions.NoSuchUser:
                                res_msg = Msg(
                                    operate=Msg.key_sendwaterball,
                                    code=ErrorCode.NoSuchUser,
                                    msg='No this user')
                            except PTT.exceptions.UserOffline:
                                res_msg = Msg(
                                    operate=Msg.key_sendwaterball,
                                    code=ErrorCode.UserOffLine,
                                    msg='User offline')
                            self.console.command.push(res_msg)

                        self.send_waterball_complete = True
                        self.send_waterball = False

                    # addfriend_id = self.command.addfriend()
                    # if addfriend_id is not None:
                    #     try:
                    #         user = self.bot.getUser(addfriend_id)
                    #
                    #         res_msg = Msg(
                    #             ErrorCode.Success,
                    #             '新增成功'
                    #         )
                    #
                    #     except PTT.exceptions.NoSuchUser:
                    #         print('無此使用者')

                time.sleep(self.console.config.quick_response_time)
                end_time = time.time()

            if not self.login:
                continue

            # 慢速輪詢區
            self.logger.show(
                Logger.DEBUG,
                '慢速輪詢')

            waterball_list = self.bot.get_waterball(
                PTT.data_type.waterball_operate_type.CLEAR
            )

            self.logger.show(
                Logger.DEBUG,
                '取得水球')

            if waterball_list is not None:
                for waterball in waterball_list:
                    if not waterball.type == PTT.data_type.waterball_type.CATCH:
                        continue

                    waterball_id = waterball.target
                    waterball_content = waterball.content
                    waterball_date = waterball.date

                    self.logger.show_value(
                        Logger.INFO,
                        f'收到來自 {waterball_id} 的水球',
                        f'[{waterball_content}][{waterball_date}]')

                    # 01/07/2020 10:46:51
                    # 02/24/2020 15:40:34
                    date_part1 = waterball_date.split(' ')[0]
                    date_part2 = waterball_date.split(' ')[1]

                    year = int(date_part1.split('/')[2])
                    month = int(date_part1.split('/')[0])
                    day = int(date_part1.split('/')[1])

                    hour = int(date_part2.split(':')[0])
                    minute = int(date_part2.split(':')[1])
                    sec = int(date_part2.split(':')[2])

                    # print(f'waterball_date {waterball_date}')
                    # print(f'year {year}')
                    # print(f'month {month}')
                    # print(f'day {day}')
                    # print(f'hour {hour}')
                    # print(f'minute {minute}')
                    # print(f'sec {sec}')

                    waterball_timestamp = int(datetime.datetime(year, month, day, hour, minute, sec).timestamp())
                    # print(f'waterball_timestamp {waterball_timestamp}')

                    payload = Msg()
                    payload.add(Msg.key_ptt_id, waterball_id)
                    payload.add(Msg.key_content, waterball_content)
                    payload.add(Msg.key_timestamp, waterball_timestamp)

                    push_msg = Msg(
                        operate=Msg.key_recvwaterball
                    )
                    push_msg.add(Msg.key_payload, payload)

                    current_dialogue_msg = Msg()
                    current_dialogue_msg.add(Msg.key_ptt_id, waterball_id)
                    current_dialogue_msg.add(Msg.key_content, waterball_content)
                    current_dialogue_msg.add(Msg.key_msg_type, 'receive')
                    current_dialogue_msg.add(Msg.key_timestamp, waterball_timestamp)

                    self.dialogue.save(current_dialogue_msg)

                    # self.dialog.recv(waterball_target, waterball_content, waterball_date)

                    for e in self.console.event.recv_waterball:
                        e(waterball_id, waterball_content, waterball_timestamp)

                    self.console.command.push(push_msg)

            new_mail = self.bot.has_new_mail()
            self.logger.show(
                Logger.DEBUG,
                '取得新信')

            if new_mail > 0 and not self.has_new_mail:
                self.has_new_mail = True
                push_msg = Msg(
                    operate=Msg.key_notify)
                push_msg.add(Msg.key_msg, f'You have {new_mail} mails')

                self.console.command.push(push_msg)
            else:
                self.has_new_mail = False

        self.logger.show(
            Logger.INFO,
            '關閉成功')
