import os
import sys
import time
import threading

from PyPtt import PTT
from SingleLog.log import Logger

from backend_util.src.console import Console
from backend_util.src.dynamic_data import DynamicData
from backend_util.src.event import EventConsole
from backend_util.src.event import Event
from backend_util.src.config import Config
from backend_util.src import config
from backend_util.src.websocketserver import WsServer
from backend_util.src.command import Command
from backend_util.src.pttadapter import PTTAdapter
from backend_util.src.crypto import Crypto
from backend_util.src.process import Process

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

    console_obj = Console()
    console_obj.role = Console.role_client

    config_obj = Config(console_obj)
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

    if '-dev' in sys.argv:
        console_obj.run_mode = 'dev'

    logger.show(
        Logger.INFO,
        '執行模式',
        console_obj.run_mode)

    logger.show(
        Logger.INFO,
        '初始化',
        '啟動')

    event_console = EventConsole(console_obj)
    console_obj.event = event_console

    event = Event(console_obj)

    comm_obj = Command(console_obj, False)
    console_obj.command = comm_obj

    comm_obj = Command(console_obj, True)
    console_obj.server_command = comm_obj

    process_obj = Process(console_obj)
    console_obj.process = process_obj

    ptt_adapter = PTTAdapter(console_obj)
    console_obj.ptt_adapter = ptt_adapter

    crypto_obj = Crypto(console_obj)
    console_obj.crypto = crypto_obj

    run_server = True


    def event_close(p):
        global run_server
        run_server = False


    client_server = WsServer(console_obj, False)
    ws_server = WsServer(console_obj, True)
    console_obj.ws_server = ws_server

    event_console.register(
        EventConsole.key_close,
        event_close)

    client_server.start()

    if client_server.start_error:
        logger.show(
            Logger.INFO,
            'websocket client-server startup error')
        event_console.execute(EventConsole.key_close)
    else:

        dynamic_data_obj = DynamicData(console_obj)
        if not dynamic_data_obj.update_state:
            logger.show(
                Logger.INFO,
                'Update dynamic data error')
            sys.exit()
        console_obj.dynamic_data = dynamic_data_obj

        ws_server.connect_setup()
        time.sleep(3)
        if ws_server.connect_server_error:
            logger.show(
                Logger.INFO,
                'websocket ws_server connect_setup error')
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
