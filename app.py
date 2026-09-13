from datetime import date, datetime
import json
import os
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, abort, jsonify, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
TARGET_USER_ID = os.getenv('LINE_USER_ID', '')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

DATA_FILE = 'progress.json'

SCHOOL_SCHEDULE = [
    {
        'id': 0,
        'school': '國立高雄科技大學 資訊管理系碩士班',
        'apply_start': date(2026, 9, 15),
        'apply_end': date(2026, 10, 6),
        'items': [
            '在學證明/學生證',
            '歷年成績單',
            '學業成績名次證明',
            '碩士學習/生涯規劃書',
            '證明自己能力或成就之各項資料影本',
        ],
    },
    {
        'id': 1,
        'school': '國立臺灣科技大學 資訊管理系碩士班 (甲、乙組)',
        'apply_start': date(2026, 9, 30),
        'apply_end': date(2026, 10, 7),
        'items': [
            '照片',
            '相關學歷證件(p.3)',
            '大學歷年成績單',
            '個人簡歷(請於上傳畫面下載表件填寫)',
            '進修計畫書',
            '推薦信(選繳)',
            '其他有助於審查之相關文件(如專題報告,獲獎是基,英文檢定...)',
        ],
    },
    {
        'id': 2,
        'school': '國立中興大學 資訊管理學系',
        'apply_start': date(2026, 10, 1),
        'apply_end': date(2026, 10, 12),
        'items': [
            '學歷證明文件',
            '歷年成績單及名次證明',
            '著作、作品或發表論文',
            '研究成果(專題報告,參與研究計畫)',
            '自傳(含就讀動機及申請動機)',
            '推薦函2封(無則免)',
            '其他有助審查資料文件',
        ],
    },
    {
        'id': 3,
        'school': '國立雲林科技大學 資訊管理系碩士班',
        'apply_start': date(2026, 9, 29),
        'apply_end': date(2026, 10, 16),
        'items': [
            '國民身分證正反面',
            '在學證明',
            '歷年成績單',
            '名次證明書',
            '推薦信2封',
            '學習研究計畫書',
            '自傳',
            '研究(專題)報告',
            (
                '其他證明文件(英文能力證明,專長證明,特殊能力,發表之學術性論文,獲獎)'
            ),
        ],
    },
    {
        'id': 4,
        'school': '國立雲林科技大學 國際人工智慧管理研究所碩士班',
        'apply_start': date(2026, 9, 29),
        'apply_end': date(2026, 10, 16),
        'items': [
            '國民身分證正反面',
            '在學證明',
            '歷年成績單',
            '英文能力證明',
            '名次證明書',
            '簡歷及自傳',
            '學習計畫書',
            '其他證明(實務專題等)',
        ],
    },
    {
        'id': 5,
        'school': '彰化師範大學 資訊管理系碩士班',
        'apply_start': date(2026, 9, 22),
        'apply_end': date(2026, 10, 7),
        'items': [
            '國民身分證正反面',
            '在學證明',
            '可資證明個人專業能力之書面資料',
        ],
    },
    {
        'id': 6,
        'school': '高雄大學 資訊管理系碩士班',
        'apply_start': date(2026, 9, 29),
        'apply_end': date(2026, 10, 19),
        'items': [
            '歷年成績單',
            '學業成績總名次證明',
            '推薦函*2',
            '履歷,自傳,學習研究計畫書,研究計畫',
            '其他有助審查資料',
        ],
    },
]


def load_progress():
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)
    except Exception:
      return {}
  return {}


def save_progress(data):
  with open(DATA_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)


@app.route('/api/progress', methods=['GET', 'POST'])
def api_progress():
  if request.method == 'POST':
    data = request.json
    save_progress(data)
    return jsonify({'status': 'success'})
  return jsonify(load_progress())


def daily_deadline_checker():
  if not TARGET_USER_ID:
    return

  today = date.today()
  progress = load_progress()
  notifications = []

  for school in SCHOOL_SCHEDULE:
    if school['apply_start'] == today:
      notifications.append(
          f"📢 【今日開始報名】\n{school['school']} 於今日開放甄試報名！"
      )

    days_left = (school['apply_end'] - today).days
    if days_left == 3:
      missing_items = []
      for idx, item in enumerate(school['items']):
        key = f"{school['id']}_{idx}"
        if not progress.get(key):
          missing_items.append(item)

      if missing_items:
        msg = (
            f"🚨 【截止倒數 3 天警告】\n{school['school']} 報名即將於"
            f" {school['apply_end']} 截止！\n目前尚未勾選項目：\n"
            + '\n'.join([f'• {i}' for i in missing_items])
            + '\n\n請儘速完成並上傳！'
        )
        notifications.append(msg)

  for text in notifications:
    try:
      line_bot_api.push_message(TARGET_USER_ID, TextSendMessage(text=text))
    except Exception as e:
      print(f'Push message failed: {e}')


scheduler = BackgroundScheduler()
scheduler.add_job(daily_deadline_checker, 'cron', hour=9, minute=0)
scheduler.start()


@app.route('/callback', methods=['POST'])
def callback():
  signature = request.headers['X-Line-Signature']
  body = request.get_data(as_text=True)
  try:
    handler.handle(body, signature)
  except InvalidSignatureError:
    abort(400)
  return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
  user_text = event.message.text
  user_id = event.source.user_id

  if user_text.strip() == '查ID':
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text=f'你的 LINE User ID 為：\n{user_id}')
    )
  elif '進度' in user_text:
    daily_deadline_checker()
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text='已為您執行最新時程與截止狀態巡查，如有即時截止未繳項目已傳送通知！'
        ),
    )
  else:
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text='輸入「查ID」可查詢個人識別碼；輸入「進度」可即時手動觸發檢查。'
        ),
    )


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port)