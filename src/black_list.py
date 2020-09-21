from single_log.log import Logger
from backend_util.src.util import sha256
from backend_util.src.msg import Msg
from backend_util.src.errorcode import ErrorCode
from backend_util.src.event import EventConsole


class BlackList:
    def __init__(self, console_boj):
        self.console = console_boj
        self.logger = Logger('BlackList', self.console.config.log_level, handler=self.console.config.log_handler)

        self.console.event.register(
            EventConsole.key_login, self.event_login)

    def event_login(self, ptt_id, ptt_pw):
        if self.is_black_user(ptt_id):
            self.logger.show(
                Logger.INFO,
                '黑名單',
                ptt_id)

            block_msg = Msg(
                operate=Msg.key_login,
                code=ErrorCode.BlackList,
                msg='block user')
            return block_msg
        return None

    def is_black_user(self, ptt_id):
        current_hash_value = sha256(ptt_id)

        return current_hash_value in self.console.dynamic_data.black_list
