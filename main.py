import json
import logging
import os
import time
import traceback
from datetime import datetime, timedelta

import itchat
import pytz
import requests
from fake_useragent import UserAgent

USE_ITCHAT = False
WECHAT_GROUP_NAME = '豆瓣开车小组'

FILE_NAME_DETECTED_IDS = 'detected_ids.txt'
FILE_NAME_SERVER_CHAN_KEY = 'sckey.key'

SLEEP_TIME_NORMAL = 6
SLEEP_TIME_WHEN_EXCEPTION = 60


def get_logger():
    logger = logging.getLogger(__name__)

    formatter = logging.Formatter("%(asctime)s: %(filename)s [line:%(lineno)d]: [%(levelname)s]: %(message)s")

    handler1 = logging.StreamHandler()
    handler2 = logging.FileHandler(filename="main.log")

    handler1.setLevel(logging.DEBUG)
    handler2.setLevel(logging.DEBUG)

    handler1.setFormatter(formatter)
    handler2.setFormatter(formatter)

    logger.addHandler(handler1)
    logger.addHandler(handler2)

    return logger


def send_msg(title, msg):
    def _send_msg_by_itchat():
        room = itchat.search_chatrooms(WECHAT_GROUP_NAME)[0]
        room.send(msg)

    def _send_msg_by_server_chan():
        with open(FILE_NAME_SERVER_CHAN_KEY) as f:
            sckey = f.read().strip()
        url = f'http://sc.ftqq.com/{sckey}.send'
        params = {
            'text': title,
            'desp': msg,
        }
        requests.get(url, params=params)

    if USE_ITCHAT:
        _send_msg_by_itchat()
    else:
        _send_msg_by_server_chan()


def is_time_ok(dt):
    if datetime.now(pytz.timezone('Asia/Shanghai')).replace(tzinfo=None) - datetime.strptime(dt, '%Y-%m-%d %H:%M:%S') < timedelta(seconds=24 * 3600):
        return True


def get_detected_ids():
    if os.path.exists(FILE_NAME_DETECTED_IDS):
        with open(FILE_NAME_DETECTED_IDS) as f:
            return json.load(f)
    return []


def set_detected_ids(ids):
    with open(FILE_NAME_DETECTED_IDS, 'w+') as f:
        json.dump(ids, f)


def main():
    logger = get_logger()

    if USE_ITCHAT:
        itchat.auto_login(hotReload=True)

    detected_ids = get_detected_ids()
    url = 'https://api.douban.com/v2/group/656297/topics?start=0&count=100'

    while True:
        time.sleep(SLEEP_TIME_NORMAL)

        try:
            headers = {'User-Agent': UserAgent().random}
            resp = requests.get(url, headers=headers)
            if resp.status_code != 200:
                logger.error(f'Got status_code: {resp.status_code}')
                logger.error(f'resp.content: {resp.content}')
                continue

            if 'json' not in resp.headers['Content-Type']:
                logger.error(f'Got Content-Type: {resp.headers["Content-Type"]}')
                logger.error(f'resp.content: {resp.content}')
                continue

            resp = resp.json()
            if 'topics' not in resp:
                logger.error(f'No topics in resp: {resp}')
                logger.error(f'json data: {resp}')
                continue

            for i in resp['topics']:
                id_ = i['id']
                title = i['title']
                url = i['alt']
                create_date = i['created']
                if '【开车】' in title and is_time_ok(create_date) and id_ not in detected_ids:
                    msg = f'{title}\n' \
                          f'{url}\n' \
                          f'发布时间：{create_date}'
                    logger.info(msg.replace('\n', '\t'))
                    send_msg(title, msg)
                    detected_ids.append(id_)
                    set_detected_ids(detected_ids)
        except Exception as e:
            logger.error(traceback.format_exc())
            continue


if __name__ == '__main__':
    main()
