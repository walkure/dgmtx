#!/usr/bin/env python3

import argparse
import configparser
import json
import pathlib
from email.parser import BytesParser
from email.policy import default
from urllib import error, request

from imapclient import IMAPClient
from imapclient.exceptions import LoginError
from oauthlib.oauth2 import BackendApplicationClient

ignore_folders = {"Sent", "Trash", "Drafts", "下書き", "ゴミ箱", "迷惑メール＿ドコモ用", "送信済み"}

parser = argparse.ArgumentParser(
    description="docomo mail to GMail Transfer tool",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    "-c",
    "--config",
    default="./config.ini",
    help="path to configuration file",
)
parser.add_argument(
    "-s", "--state", default="./laststate.json", help="path to state file"
)
args = parser.parse_args()

conf = configparser.ConfigParser()

conf.read(pathlib.Path(args.config), "UTF-8")

laststate_file = pathlib.Path(args.state + "")


def get_access_token(client_id, client_secret, refresh_token):
    oauth = BackendApplicationClient(client_id)
    url, headers, body = oauth.prepare_refresh_token_request(
        "https://accounts.google.com/o/oauth2/token",
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
    )
    req = request.Request(url, body.encode("us-ascii"), headers=headers)
    with request.urlopen(req) as res:
        obj = json.loads(res.read().decode("us-ascii"))
    return obj["access_token"]


def fetch_folder(source, dest1, dest2, folder, past_uid):
    status = source.folder_status(folder, ["UIDNEXT"])
    print("Folder:", folder, " past_uid:", past_uid, " uidnext:", status[b"UIDNEXT"])

    source.select_folder(folder, True)  # read-only
    uids = source.search(["UID", "{}:{}".format(past_uid, status[b"UIDNEXT"])])
    uids.sort()

    print(uids)
    if len(uids) == 0:
        return past_uid, None

    new_arrivals = []
    for uid in uids:
        new_arrivals.append(transfer_mail(source, dest1, dest2, folder, uid))

    return uids[-1] + 1, new_arrivals


def transfer_mail(source, dest1, dest2, folder, uid):
    resp = source.fetch(
        [uid], ["RFC822", "INTERNALDATE", "BODY[HEADER.FIELDS (SUBJECT FROM)]"]
    )
    body = resp[uid][b"RFC822"].decode("us-ascii")
    idate = resp[uid][b"INTERNALDATE"]
    headers = BytesParser(policy=default).parsebytes(
        resp[uid][b"BODY[HEADER.FIELDS (SUBJECT FROM)]"], True
    )

    if not dest1.folder_exists(folder):
        dest1.create_folder(folder)
    print("append uid:", uid)
    # dest.append(folder,body,flags=(br"\Recent"),msg_time=idate)
    dest1.append(folder, body, msg_time=idate)

    if dest2 is not None:
        dest2.append("INBOX", body, msg_time=idate)

    return {"subject": headers["subject"], "from": headers["from"], "folder": folder}


def send_new_arrival_notify(new_arrivals):
    if len(new_arrivals) == 0:
        return
    if "slack" not in conf:
        return
    obj = {"attachments": []}
    for datum in new_arrivals:
        block = {"type": "section", "fields": []}
        block["fields"].append({"title": "IN", "value": datum["folder"], "short": True})
        block["fields"].append({"title": "From", "value": datum["from"], "short": True})
        block["fields"].append(
            {"title": "件名", "value": datum["subject"], "short": True}
        )
        obj["attachments"].append(block)

    payload = json.dumps(obj).encode("utf-8")

    req = request.Request(
        conf["slack"]["endpoint"],
        data=payload,
        method="POST",
        headers={"content-type": "application/json", "User-Agent": ""},
    )

    try:
        with request.urlopen(req) as response:
            body = response.read().decode("utf-8")
            print(body)
    except error.HTTPError as e:
        print("Error:" + e)


def login_gmail(client, access_token):
    if access_token is None:
        print("fetch access token")
        access_token = get_access_token(
            conf["gmail"]["client_id"],
            conf["gmail"]["client_secret"],
            conf["gmail"]["refresh_token"],
        )

    try:
        client.oauthbearer_login(conf["gmail"]["address"], access_token)
        return access_token

    except LoginError:
        print("update access token")
        access_token = get_access_token(
            conf["gmail"]["client_id"],
            conf["gmail"]["client_secret"],
            conf["gmail"]["refresh_token"],
        )
        client.oauthbearer_login(conf["gmail"]["address"], access_token)
        return access_token


def main():
    if laststate_file.exists():
        with open(str(laststate_file)) as file:
            last_states = json.load(file)
    else:
        last_states = {}

    new_arrivals_all = []
    with IMAPClient(host="imap.spmode.ne.jp") as source, IMAPClient(
        host="imap.googlemail.com"
    ) as gmail, IMAPClient(host="outlook.office365.com") as office:

        source.login(conf["spmode"]["user"], conf["spmode"]["pass"])
        last_states["access_token"] = login_gmail(gmail, last_states["access_token"])
        office_or_none = None
        if "outlook" in conf:
            office.login(conf["outlook"]["user"], conf["outlook"]["pass"])
            office_or_none = office

        # print(dest.capabilities())
        for folder in source.list_folders():
            if folder[2] in ignore_folders:
                continue

            last_uid = 1
            if folder[2] in last_states:
                last_uid = last_states[folder[2]]

            uid, new_arrivals = fetch_folder(
                source, gmail, office_or_none, folder[2], last_uid
            )
            print("new last uid:", uid)
            last_states[folder[2]] = uid
            if new_arrivals is not None:
                new_arrivals_all += new_arrivals

    with open(str(laststate_file), "w") as file:
        json.dump(last_states, file)

    send_new_arrival_notify(new_arrivals_all)


if __name__ == "__main__":
    main()
