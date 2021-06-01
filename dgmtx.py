#!/usr/bin/python3

from imapclient import IMAPClient
from imapclient.exceptions import LoginError
from oauthlib.oauth2 import BackendApplicationClient
import urllib.request
import json
import pathlib
import configparser

ignore_folders = {'Sent', 'Trash', 'Drafts',
                  '下書き', 'ゴミ箱', '迷惑メール＿ドコモ用', '送信済み'}


conf = configparser.ConfigParser()
conf.read('./config.ini', 'UTF-8')

laststate_file = pathlib.Path('./laststate.json')


def fetch_folder(source, dest, folder, past_uid):
    status = source.folder_status(folder, ['UIDNEXT'])
    print("Folder:", folder, " past_uid:",
          past_uid, ' uidnext:', status[b'UIDNEXT'])

    source.select_folder(folder, True)  # read-only
    uids = source.search(['UID', '{}:{}'.format(past_uid, status[b'UIDNEXT'])])
    uids.sort()

    print(uids)
    if len(uids) == 0:
        return past_uid

    for uid in uids:
        transfer_mail(source, dest, folder, uid)

    return uids[-1] + 1


def transfer_mail(source, dest, folder, uid):
    resp = source.fetch([uid], ['RFC822', 'INTERNALDATE'])
    body = resp[uid][b'RFC822'].decode('us-ascii')
    idate = resp[uid][b'INTERNALDATE']

    if not dest.folder_exists(folder):
        dest.create_folder(folder)
    print('append uid:', uid)
    # dest.append(folder,body,flags=(br"\Recent"),msg_time=idate)
    dest.append(folder, body, msg_time=idate)


def get_access_token(client_id, client_secret, refresh_token):
    oauth = BackendApplicationClient(client_id)
    url, headers, body = oauth.prepare_refresh_token_request('https://accounts.google.com/o/oauth2/token',
                                                             client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)
    req = urllib.request.Request(url, body.encode('us-ascii'), headers=headers)
    with urllib.request.urlopen(req) as res:
        obj = json.loads(res.read().decode('us-ascii'))
    return obj['access_token']


if laststate_file.exists():
    with open(str(laststate_file)) as file:
        last_states = json.load(file)
else:
    last_states = {}

with IMAPClient(host='imap.spmode.ne.jp') as source:
    source.login(conf['spmode']['user'], conf['spmode']['pass'])

    with IMAPClient(host='imap.googlemail.com') as dest:

        if 'access_token' not in last_states:
            print('fetch access token')
            last_states['access_token'] = get_access_token(conf['gmail']['client_id'], conf['gmail']['client_secret'], conf['gmail']['refresh_token'])
        
        try:
            dest.oauthbearer_login(conf['gmail']['address'],last_states['access_token'])
        except LoginError as e:
            print('update access token')
            last_states['access_token'] = get_access_token(conf['gmail']['client_id'], conf['gmail']['client_secret'], conf['gmail']['refresh_token'])
            dest.oauthbearer_login(conf['gmail']['address'],last_states['access_token'])
            
        # print(dest.capabilities())

        for folder in source.list_folders():
            if folder[2] in ignore_folders:
                continue

            last_uid = 1
            if folder[2] in last_states:
                last_uid = last_states[folder[2]]

            uid = fetch_folder(source, dest, folder[2], last_uid)
            print('new last uid:', uid)
            last_states[folder[2]] = uid

with open(str(laststate_file), 'w') as file:
    json.dump(last_states, file)
