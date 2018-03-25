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
    print(event)
    user_name = get_user_name(event.source)
    print(user_name)
    lines = event.message.text.split("\n")
    msgs = []
    for line in lines:
      msgs.append(user_name + roll_message(line))
    msg = "\n".join(msgs)
    if msg is None:
        abort(400)
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )

def roll_message(roll_str):
    print(roll_str)
    if roll_str is None and len(roll_str) == 0 and not isinstance(roll_str, str):
        return None
    roll = mojimoji.zen_to_han(roll_str).lower()
    if "<" in roll or ">" in roll or "=" in roll:
        msg = hantei_roll(roll)
    else:
        msg = dice_roll(roll)
    return msg

def hantei_roll(roll):
    roll_dice, opr, obj_point = re.sub(" *([^0-9]*[<>=][^0-9]*) *", "\t\\1\t", roll).split("\t")
    deme, deme_sum = dice_roll(roll_dice).split(" = ")[1:]
    is_success = success(int(deme_sum), int(obj_point), opr)
    msg = "%s = %s = %s %s %s %s" % (roll_dice, str(deme), deme_sum, opr, obj_point, is_success)
    return msg

def dice_roll(roll):
    num, dice = split_dice(roll)
    if num is None:
        return None
    result = rolling(num, dice)
    return "%s = %s = %d" % (roll, str(result), sum(result))

def split_dice(msg):
    split = msg.split("d")
    if len(split) != 2 or not split[0].isdigit() or not split[1].isdigit():
        return None, None
    return split

def rolling(num, dice):
    return [random.randint(1,int(dice)) for _ in range(int(num))]

def success(deme, obj_point, operater):
    operater = operater.strip()
    print(operater)
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
        is_success = deme >= obj_point
    else:
        is_success = None
    return results[is_success]

def get_user_name(source):
    chat_type = source.type
    if chat_type == "group":
        group_id = source.group_id
        user_id = source.user_id
        user_info = line_bot_api.get_group_member_profile(group_id, user_id)
        user_name = user_info.display_name + ": "
    elif chat_type == "room":
        room_id = source.room_id
        user_id = source.user_id
        user_info = line_bot_api.get_room_member_profile(room_id, user_id)
        user_name = user_info.display_name + ": "
    else:
        user_name = ""
    return user_name

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
