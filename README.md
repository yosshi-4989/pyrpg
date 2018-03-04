# Lineダイスボット

Herokuへのデプロイ
<pre>
$ heroku login
$ heroku create heroku-line-bot
$ heroku config:set LINE_CHANNEL_SECRET="<Channel Secret>"
$ heroku config:set LINE_CHANNEL_ACCESS_TOKEN="<アクセストークン>"
$ git push heroku master
</pre>

返答する文字列を変更する場合は、以下のコードを修正する
```python
@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    # 送信メッセージの作成
    msg = roll_message(event.message.text)
    if msg is None:
        # 送信しない場合、これを返す
        abort(400)
    else:
        # 送信する場合、TextSendMessage(text="送りたい文字列")を設定する
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
```
