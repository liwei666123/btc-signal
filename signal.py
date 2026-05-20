import os
import json
import requests
import pandas as pd
import ta
from datetime import datetime

print("程序开始运行")

密钥 = os.environ.get('DEEPSEEK_API_KEY', '')
print(f"密钥是否存在: {bool(密钥)}")

if not 密钥:
    print("错误：没有找到DeepSeek密钥")
    信号 = {
        '价格': 0,
        'RSI': 0,
        '操作': '错误',
        '置信度': 0,
        '理由': '未设置DeepSeek密钥',
        '更新时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
else:
    try:
        print("正在获取币安数据...")
        网址 = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=100"
        响应 = requests.get(网址, timeout=15)
        数据 = 响应.json()
        收盘价列表 = [float(c[4]) for c in 数据]
        数据表 = pd.DataFrame({'close': 收盘价列表})
        数据表['rsi'] = ta.momentum.RSIIndicator(数据表['close'], window=14).rsi()
        当前价格 = 数据表['close'].iloc[-1]
        RSI值 = 数据表['rsi'].iloc[-1]
        if RSI值 != RSI值:
            RSI值 = 50
        print(f"价格: {当前价格}, RSI: {RSI值}")

        print("正在调用DeepSeek AI...")
        提示词 = f"比特币当前价格{当前价格:.2f}美元，14周期RSI为{RSI值:.1f}。请给出买入、卖出或持有建议，输出JSON格式: {{\"操作\":\"买入/卖出/持有\", \"置信度\":0-100, \"理由\":\"简要分析\"}}"
        请求头 = {"Authorization": f"Bearer {密钥}", "Content-Type": "application/json"}
        请求体 = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": 提示词}],
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }
        API响应 = requests.post("https://api.deepseek.com/v1/chat/completions", headers=请求头, json=请求体, timeout=30)
        API响应.raise_for_status()
        结果 = API响应.json()
        AI回复 = json.loads(结果["choices"][0]["message"]["content"])
        信号 = {
            '价格': round(当前价格, 2),
            'RSI': round(RSI值, 1),
            '操作': AI回复.get('操作', '持有'),
            '置信度': AI回复.get('置信度', 50),
            '理由': AI回复.get('理由', '无'),
            '更新时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        print("AI调用成功")
    except Exception as e:
        print(f"发生错误: {e}")
        信号 = {
            '价格': 0,
            'RSI': 0,
            '操作': '错误',
            '置信度': 0,
            '理由': f'程序出错: {str(e)}',
            '更新时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

网页内容 = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI比特币信号</title>
<style>
body{{font-family:Arial;text-align:center;padding:20px;background:#0a0e27;color:white;}}
.card{{background:#1e2a3a;border-radius:20px;padding:20px;margin:10px auto;max-width:500px;}}
.price{{font-size:2em;color:#ffd966;}}
.rsi{{font-size:1.5em;}}
.action{{font-size:2em;margin:20px;padding:15px;border-radius:40px;}}
.买入{{background-color:#2e7d32;}}
.卖出{{background-color:#c62828;}}
.持有{{background-color:#ff8f00;}}
.error{{background-color:#555;}}
.reason{{background:#00000066;padding:10px;border-radius:12px;}}
.time{{font-size:0.8em;color:#aaa;}}
</style>
</head>
<body>
<div class="card">
<h1>🤖 AI实时量化信号</h1>
<div class="price">💰 价格: ${信号['价格']}</div>
<div class="rsi">📊 RSI: {信号['RSI']}</div>
<div class="action {信号['操作']}">📈 操作: {信号['操作']}<br>🎯 置信度: {信号['置信度']}%</div>
<div class="reason">💡 理由: {信号['理由']}</div>
<div class="time">🕒 更新时间: {信号['更新时间']}</div>
</div>
<div class="card"><small>每小时自动更新 | 数据: 币安 | AI: DeepSeek</small></div>
</body>
</html>'''

with open('网页.html', 'w', encoding='utf-8') as 文件:
    文件.write(网页内容)
print("网页文件已生成")
