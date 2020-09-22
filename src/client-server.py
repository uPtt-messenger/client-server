import os
import sys
import time
import threading

from PyPtt import PTT
from SingleLog.log import Logger

from backend_util.src.console import Console
from backend_util.src.dynamic_data import DynamicData
from backend_util.src.event import EventConsole
from backend_util.src.config import Config
from backend_util.src import config
from backend_util.src.websocketserver import WsServer

from command import Command
from pttadapter import PTT_Adapter
from feedback import Feedback

from black_list import BlackList

log_path = None


def log_to_file(msg):
    global log_path
    if log_path is None:
        desktop = os.path.join(
            os.path.join(
                os.environ['USERPROFILE']
            ),
            'Desktop')

        log_path = f'{desktop}/uPtt_log.txt'

        print(log_path)

    with open(log_path, 'a', encoding='utf8') as f:
        f.write(f'{msg}\n')


if __name__ == '__main__':

    if '-debug' in sys.argv:
        config.log_handler = log_to_file
        config.log_level = Logger.TRACE

    config_obj = Config()

    console_obj = Console()
    console_obj.config = config_obj

    if len(sys.argv) > 1:
        print(sys.argv)

    if '-debug' in sys.argv:
        config_obj.log_level = Logger.TRACE
        config_obj.log_handler = log_to_file

        config_obj.ptt_log_level = PTT.log.level.TRACE
        config_obj.log_handler = log_to_file

    logger = Logger('Client-server', config.log_level, handler=console_obj.config.log_handler)

    logger.show(
        Logger.INFO,
        'uPtt 版本',
        config_obj.version)

    logger.show(
        Logger.INFO,
        '初始化',
        '啟動')

    if '-dev' in sys.argv:
        console_obj.run_mode = 'dev'

    logger.show(
        Logger.INFO,
        '執行模式',
        console_obj.run_mode)

    event_console = EventConsole(console_obj)
    console_obj.event = event_console

    dynamic_data_obj = DynamicData(console_obj)
    if not dynamic_data_obj.update_state:
        logger.show(
            Logger.INFO,
            'Update dynamic data error')
        sys.exit()
    console_obj.dynamic_data = dynamic_data_obj

    comm_obj = Command(console_obj)
    console_obj.command = comm_obj

    black_list = BlackList(console_obj)

    feedback = Feedback(console_obj)
    ptt_adapter = PTT_Adapter(console_obj)

    run_server = True

    def event_close(p):
        global run_server
        run_server = False

    ws_server = WsServer(console_obj)

    event_console.register(
        EventConsole.key_close,
        ws_server.stop)

    event_console.register(
        EventConsole.key_close,
        event_close)

    ws_server.start()

    if ws_server.start_error:
        logger.show(
            Logger.INFO,
            'websocket client-server startup error')
        event_console.execute(EventConsole.key_close)
    else:

        logger.show(
            Logger.INFO,
            '初始化',
            '完成')

        while run_server:
            try:
                time.sleep(0.5)
            except KeyboardInterrupt:
                event_console.execute(EventConsole.key_close)
                break

    logger.show(
        Logger.INFO,
        '執行最終終止程序')

    running = threading.Event()
    running.set()
    running.clear()

    logger.show(
        Logger.INFO,
        '最終終止程序全數完成')
