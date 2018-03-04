# -*- coding: utf-8 -*-
import os
import sys
import random
import mojimoji
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (MessageEvent, TextMessage, TextSendMessage,)

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', "")
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', "")
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
    mess = roll_message(event.message.text)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=mess)
    )

def roll_message(roll_str):
    if roll_str is None and len(roll_str) == 0 and not isinstance(roll_str, str):
        return None
    roll = mojimoji.zen_to_han(roll_str).lower()
    split = roll.split("d")
    if len(split) != 2 and split[0].isdigit() and split[1].isdigit():
        return None
    ress, sum = diceroll(*split)
    return "%s = %d" % (str(ress), sum)

def diceroll(num, d):
    res = [random.randint(1,int(d)) for i in range(int(num))]
    return res, sum(res)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
