from flask import Flask
from threading import Thread
import os

app = Flask('')

# 必須有一個路由讓 Render 檢查服務是否健康
@app.route('/')
def home():
    return "Bot is running!"

def run():
    # Render 預設使用 PORT 環境變數，通常是 8080
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    # 在一個單獨的線程中啟動 Flask Web 伺服器
    t = Thread(target=run)
    t.start()