import os
from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 請把下面的 "你的_Channel_access_token" 換成你在 LINE Developers 取得的真實 Token
LINE_CHANNEL_ACCESS_TOKEN = os.getenv(
    'LINE_CHANNEL_ACCESS_TOKEN', '8NaGHCMptM1YYpJURCwLgzNG5u0AdQbBCP/S366vLDkC1CJfqAbF5+CMcBT069AhjL6J19X5DLeW5epcz9qWekzmdbA2cI+SnUoRHGWI7U/tkEOlxELjWil8Q4o2V9QClPUzgO+WGs5AttK4xooB/gdB04t89/1O/w1cDnyilFU='
)
LINE_CHANNEL_SECRET = os.getenv(
    'LINE_CHANNEL_SECRET', '3ce25bbc57e214ce6fe66a3e9dcf757e'
)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


@app.route('/callback', methods=['POST'])
def callback():
  signature = request.headers['X-Line-Signature']
  body = request.get_data(as_text=True)
  app.logger.info('Request body: ' + body)
  try:
    handler.handle(body, signature)
  except InvalidSignatureError:
    abort(400)
  return 'OK'


# 當你在 LINE 傳訊息給機器人時，它會執行這裡
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
  user_text = event.message.text

  if '進度' in user_text:
    reply_text = (
        '🎓 【研究所甄試報名管家】\n'
        '目前監控中的校系清單：\n'
        '1. 國立高雄科技大學資管 (截止 10/06)\n'
        '2. 國立臺灣科技大學資管 (截止 10/07)\n'
        '3. 國立中興大學資管 (截止 10/12)\n'
        '4. 國立雲林科技大學資管 (截止 10/16)\n'
        '5. 國立雲林科技大學國智所 (截止 10/16)\n\n'
        '請隨時至網頁介面勾選備審資料進度！'
    )
  else:
    reply_text = (
        f'你傳給機器人的訊息是：「{user_text}」\n'
        '輸入「進度」可以查詢目前各校報名與截止時間喔！'
    )

  line_bot_api.reply_message(
      event.reply_token, TextSendMessage(text=reply_text)
  )


if __name__ == '__main__':
  # 支援雲端平台動態 Port（若在本地測試則預設 5000）
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port)