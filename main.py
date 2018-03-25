# -*- coding: utf-8 -*-
import os
import sys

import re
import random
import mojimoji

from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookHandler, )
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (MessageEvent, TextMessage, TextSendMessage,)

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    user_name = get_user_name(event.source)
    lines = event.message.text.split("\n")
    msgs = []
    for line in lines:
        msg = make_message(line)
        if msg is not  None:
            msgs.append(msg)

    if msgs is None or len(msgs) == 0:
        abort(400)
    else:
        msg = user_name + "\n".join(msgs)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )

def make_message(text):
    if text is None and len(text) == 0 and not isinstance(text, str):
        return None
    lower_text = mojimoji.zen_to_han(text).lower()

    if lower_text.startswith("dcoc "):
        return roll_coc(lower_text)
    #if lower_text.startswith("dsf "):
    #    return roll_sf(lower_text)

    dice_str, opr, opt = parse_text_to_dice_str(lower_text)
    if dice_str is None:
        return None
    if opr is not None:
        dice_str, res, opr, is_succ = hantei_roll(dice_str, opr)
        return "%s = %s = %d %s -> %s" % (dice_str, str(res), sum(res), opr, is_succ)
    dice_str, res = roll_dice_str(dice_str)
    return "%s = %s = %d" % (dice_str, str(res), sum(res))

dice_pattern = re.compile("[0-9]*d[0-9]*")
operation_pattern = re.compile("[<>=][<>=]* *[0-9][0-9]*")
opr_split_pattern = re.compile("([<>=]) *([0-9])")
def parse_text_to_dice_str(text):
    # ダイスの存在確認
    match = dice_pattern.match(text.strip())
    if match is None: # 存在しないときは無視する
        return None
    dice_str = match.group()
    option = text[match.end():].strip()

    # 判定器が存在するかの確認
    match = operation_pattern.match(option)
    if match is None:
        return dice_str, None, option
    operater = match.group()
    add_str = option[match.end():]
    return dice_str, operater, add_str

def split_opr_and_obj(opr):
    return opr_split_pattern.sub("\\1 \\2", opr).split()

def hantei_roll(dice_str, opr):
    opr, obj = split_opr_and_obj(opr)
    dice_str, roll_result = roll_dice_str(dice_str)
    is_success = success(sum(roll_result), int(obj), opr)
    return dice_str, roll_result, "%s %s" % (opr, obj), is_success
    #msg = "%s = %s = %s %s %s %s" % (dice_str, str(deme), deme_sum, opr, obj_point, is_success)
    #return msg

def roll_dice_str(dice_str):
    num, dice = split_dice(dice_str)
    if num is None:
        return None
    return "%sd%s" % (num, dice), roll_dices(int(num), int(dice))

def split_dice(dice_str):
    if dice_str is None:
        return None
    split = dice_str.split("d")
    if len(split) != 2:
        return None
    if split[0] == "" or not split[0].isdigit():
        split[0] = "1"
    if split[1] == "" or not split[1].isdigit():
        split[1] = "6"
    return split

def roll_dices(num, dice):
    return [roll_dice(dice) for _ in range(num)]

def roll_dice(dice):
    return random.randint(1, dice)

def success(deme, obj_point, operater):
    operater = operater.strip()
    results = {True: "成功", False: "失敗", None: "不明"}
    is_success = None
    if operater == "<=":
        is_success = deme <= obj_point
    elif operater == "<":
        is_success = deme < obj_point
    elif operater == ">":
        is_success = deme > obj_point
    elif operater == ">=":
        is_success = deme >= obj_point
    elif operater == "=":
        is_success = deme == obj_point
    else:
        is_success = None
    return results[is_success]

def get_user_name(source):
    chat_type = source.type
    if chat_type == "group":
        group_id = source.group_id
        user_id = source.user_id
        user_info = line_bot_api.get_group_member_profile(group_id, user_id)
        user_name = user_info.display_name + "\n"
    elif chat_type == "room":
        room_id = source.room_id
        user_id = source.user_id
        user_info = line_bot_api.get_room_member_profile(room_id, user_id)
        user_name = user_info.display_name + "\n"
    else:
        user_name = ""
    return user_name

def roll_coc(roll):
    obj_point = roll.split()[1]
    roll_val = roll_dices(1, 100)[0]

    if obj_point.isdigit():
        point = int(obj_point)
        msg = result_coc(roll_val, point)
    else:
        return "1d100 = %d" % roll_val
    return "1d100 = %d <= %s -> %s" % (roll_val, obj_point, msg)

CRITICAL_MESSAGE = {
    True: "クリティカル",
    False: "失敗"
}
FUMBLE_MESSAGE = {
    True: "成功",
    False: "ファンブル"
}
RESULT_MESSAGE = {
    True: "成功",
    False: "失敗"
}
def result_coc(val, obj):
    msgs = []
    is_success = val <= obj
    if val <= 5:
        msgs.append(CRITICAL_MESSAGE[is_success])
    if val <= (obj / 5):
        msgs.append("スペシャル")
    if val >= 96:
        msgs.append(FUMBLE_MESSAGE[is_success])
    if len(msgs) == 0:
        return RESULT_MESSAGE[is_success]
    return "/".join(msgs)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
