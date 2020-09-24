import time
from datetime import datetime, timedelta

import itchat
import pytz
import requests

USE_ITCHAT = True

if USE_ITCHAT:
    itchat.auto_login()


def send_msg_by_itchat(msg):
    room = itchat.search_chatrooms('神经病吧这个人！')[0]
    room.send(msg)


def send_msg_by_server_chan(title, msg):
    with open('sckey.key') as f:
        sckey = f.read().strip()
    url = f'http://sc.ftqq.com/{sckey}.send'
    params = {
        'text': title,
        'desp': msg,
    }
    resp = requests.get(url, params=params)
    return resp


def is_time_ok(dt):
    if datetime.now(pytz.timezone('Asia/Shanghai')).replace(tzinfo=None) - datetime.strptime(dt, '%Y-%m-%d %H:%M:%S') < timedelta(seconds=24 * 3600):
        return True


def main():
    detected_ids = set()
    while True:
        for start in range(0, 100, 100):  # for page iter
            url = f'https://api.douban.com/v2/group/656297/topics?start={start}&count={start + 100}'
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36 Edg/79.0.309.56'}
            resp = requests.get(url, headers=headers).json()
            for i in resp['topics']:
                id_ = i['id']
                create_date = i['created']
                update_date = i['updated']
                title = i['title']
                url = i['alt']
                if '【开车】' in title and is_time_ok(create_date) and id_ not in detected_ids:
                    if USE_ITCHAT:
                        msg = f'{title}\n' \
                              f'{url}\n' \
                              f'发布时间：{create_date}'
                        send_msg_by_itchat(msg)
                    else:
                        send_msg_by_server_chan(title, url)
                    detected_ids.add(id_)
                    print(f'id: {id_}\tcreate_date: {create_date}\tupdate_date: {update_date}\ttitle: {title}')
        time.sleep(60)


if __name__ == '__main__':
    main()
