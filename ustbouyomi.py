# -*- coding:utf-8 -*-

import re
import sys
import subprocess
import functools
import argparse
import configparser
import urllib.request
import json
import asyncio


def url_data(name):
    return 'http://api.ustream.tv/json/channel/%s' % name


def url_socialstream(id):
    return 'http://socialstream.ustream.tv/socialstream/get.json/%d' % id


def get_json(url):
    res = urllib.request.urlopen(url)
    return json.loads(res.read().decode('utf-8'))


def get_channel_info(name):
    return get_json(url_data(name) + '/getInfo')


def get_timeslice(name):
    return get_json(url_data(name) + '/getInfo')


def bouyomi(data, obj):
    if obj['range'][0] > 0:
        for payload in obj['payload']:
            if 'text' in payload:
                m = re.match('(.+) \(live at.+', payload['text'], flags=re.IGNORECASE)
                if m:
                    user = payload['profileUserName']
                    text = m.group(1)

                    print('%s: %s' % (user, text))

                    config = data['config']['DEFAULT']
                    path = config['RemoteTalkPath']
                    option = config['RemoteTalkOption'].strip().split(' ')

                    cmd = list([path])
                    for p in option:
                        cmd.append(p.replace('{text}', text))

                    try:
                        subprocess.Popen(cmd, stdout=subprocess.DEVNULL)
                    except:
                        print(e.message)
                        pass



def timeslice(loop, data):
    try:
        if data['timestamp'] == 0:
            url = '%s/default' % (url_socialstream(data['channel_id']))
        else:
            url = '%s/timeslice/%d/%d' % (url_socialstream(data['channel_id']), data['timestamp'], data['refreshInterval'])

        obj = get_json(url)

        bouyomi(data, obj)

        data['timestamp'] = obj['range'][1]
        data['refreshInterval'] = obj['refreshInterval']

        if data['refreshInterval'] == 0:
            data['refreshInterval'] = 10

        loop.call_later(data['refreshInterval'], timeslice, loop, data)

    except Exception as e:
        print(e.message)
        loop.stop()


def main():

    p = argparse.ArgumentParser(description='To speak Ustream socialstream.')
    p.add_argument('id', help='Channel ID(0123456) / URL(http://www.ustream.tv/channel/CHANNEL)')
    args = p.parse_args()

    channel_id = args.id

    m1 = re.match('(http|https)+:\/\/(www\.)*ustream\.tv\/channel\/(.+)', args.id, flags=re.IGNORECASE)
    if m1:
        if m1.lastindex >= 3:
            channel_name = m1.group(3)
            print('channel name: %s' % channel_name)
            channel_info = get_channel_info(channel_name)
            channel_id = channel_info['results']['id']
    else:
        channel_id = args.id

    print('channel id: %s' % channel_id)

    config = configparser.ConfigParser()
    config.read('config.ini')

    data = {'config': config, 'channel_id': channel_id, 'timestamp': 0, 'refreshInterval': 10}

    loop = asyncio.get_event_loop()
    loop.call_soon(timeslice, loop, data)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.stop()


if __name__ == '__main__':
    main()
