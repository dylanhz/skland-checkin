import json
import os.path
import time
import logging
import requests

from datetime import date

app_code = "4ca99fa6b56cc2ba"
token_env = os.environ.get("TOKEN")
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


def config_logger():
    current_date = date.today().strftime("%Y-%m-%d")
    if not os.path.exists("logs"):
        os.mkdir("logs")
    logger = logging.getLogger()

    file_handler = logging.FileHandler(f"./logs/{current_date}.log", encoding="utf-8")
    logger.addHandler(file_handler)
    logging.getLogger().setLevel(logging.DEBUG)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)

    def filter_code(text):
        filter_key = ["code", "cred", "token"]
        try:
            j = json.loads(text)
            if not j.get("data"):
                return text
            data = j["data"]
            for i in filter_key:
                if i in data:
                    data[i] = "*****"
            return json.dumps(j, ensure_ascii=False)
        except:
            return text

    _get = requests.get
    _post = requests.post

    def get(*args, **kwargs):
        response = _get(*args, **kwargs)
        logger.info(
            f"GET {args[0]} - {response.status_code} - {filter_code(response.text)}"
        )
        return response

    def post(*args, **kwargs):
        response = _post(*args, **kwargs)
        logger.info(
            f"POST {args[0]} - {response.status_code} - {filter_code(response.text)}"
        )
        return response

    # 替换 requests 中的方法
    requests.get = get
    requests.post = post


def get_cred_by_token(token):
    grant_code = get_grant_code(token)
    return get_cred(grant_code)


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
        print(f"requesting user list failed: {resp['message']}")
        if resp.get("message") == "用户未登录":
            print(f"login expired, rerun.")
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
            print(
                f'user {i.get("nickName")}({i.get("channelName")}) check-in failed, reason: {resp.get("message")}'
            )
            continue
        awards = resp["data"]["awards"]
        for j in awards:
            res = j["resource"]
            print(
                f'user {i.get("nickName")}({i.get("channelName")}) check-in succeed, get {res["name"]}x{j.get("count") or 1}'
            )


def get_token():
    v = []
    token_list = token_env.split(",")
    for i in token_list:
        v.append(i)
    print(f"{len(v)} tokens read")
    return v


def start():
    token = get_token()
    for i in token:
        try:
            check_in(get_cred_by_token(i))
        except Exception as ex:
            print(f"check-in failed, reason: {str(ex)}")
            logging.error("", exc_info=ex)


config_logger()

logging.info("=========starting==========")

start_time = time.time()
start()
end_time = time.time()
logging.info(f"complete with {(end_time - start_time) * 1000} ms")
logging.info("==========ending===========")
