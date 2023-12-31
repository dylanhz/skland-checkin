import os
import sys
import logging
import requests


app_code = "4ca99fa6b56cc2ba"
header = {
    "cred": "",
    "User-Agent": "Skland/1.0.1 (com.hypergryph.skland; build:100001014; Android 31; ) Okhttp/4.11.0",
    "Accept-Encoding": "gzip",
    "Connection": "close",
    "vName": "1.0.1",
    "vCode": "100001014",
    "dId": "de9759a5afaa634f",
    "platform": "1",
}
header_login = {
    "User-Agent": "Skland/1.0.1 (com.hypergryph.skland; build:100001014; Android 31; ) Okhttp/4.11.0",
    "Accept-Encoding": "gzip",
    "Connection": "close",
    "vName": "1.0.1",
    "vCode": "100001014",
    "dId": "de9759a5afaa634f",
    "platform": "1",
}
sign_url = "https://zonai.skland.com/api/v1/game/attendance"
binding_url = "https://zonai.skland.com/api/v1/game/player/binding"
grant_code_url = "https://as.hypergryph.com/user/oauth2/v2/grant"
cred_code_url = "https://zonai.skland.com/api/v1/user/auth/generate_cred_by_code"


def get_cred_by_token(token):
    grant_code = get_grant_code(token)
    cred = get_cred(grant_code)
    return cred


def get_grant_code(token):
    response = requests.post(
        grant_code_url,
        json={"appCode": app_code, "token": token, "type": 0},
        headers=header_login,
    )
    resp = response.json()
    if response.status_code != 200:
        raise Exception(f"getting grant failed: {resp}")
    if resp.get("status") != 0:
        raise Exception(f'getting grant failed: {resp["msg"]}')
    return resp["data"]["code"]


def get_cred(grant):
    resp = requests.post(
        cred_code_url, json={"code": grant, "kind": 1}, headers=header_login
    ).json()
    if resp["code"] != 0:
        raise Exception(f'getting cred failed: {resp["message"]}')
    return resp["data"]["cred"]


def get_binding_list():
    v = []
    resp = requests.get(binding_url, headers=header).json()
    if resp["code"] != 0:
        logging.warning(f"requesting user list failed: {resp['message']}")
        if resp.get("message") == "用户未登录":
            logging.warning(f"login expired, rerun.")
            return []
    for i in resp["data"]["list"]:
        if i.get("appCode") != "arknights":
            continue
        v.extend(i.get("bindingList"))
    return v


def check_in(cred):
    header["cred"] = cred
    characters = get_binding_list()

    for i in characters:
        body = {"uid": i.get("uid"), "gameId": 1}
        resp = requests.post(sign_url, headers=header, json=body).json()
        if resp["code"] != 0:
            logging.info(
                f'{i.get("nickName")}({i.get("channelName")}) check-in failed, reason: {resp.get("message")}'
            )
        else:
            awards = resp["data"]["awards"]
            for j in awards:
                res = j["resource"]
                logging.info(
                    f'{i.get("nickName")}({i.get("channelName")}) check-in succeed, get {res["name"]} x {j.get("count") or 1}'
                )


if __name__ == "__main__":
    log_path = f"{os.path.dirname(__file__)}/skland.log"
    logging.basicConfig(
        filename=log_path,
        filemode="a",
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO,
        encoding="utf-8",
    )

    token = sys.argv[1]
    try:
        check_in(get_cred_by_token(token))
    except Exception as ex:
        logging.error(f"check-in failed, reason: {str(ex)}")
