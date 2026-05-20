import os
import json
import requests
import pandas as pd
import ta
from datetime import datetime
import math

print("程序开始运行")

api_key = os.environ.get('DEEPSEEK_API_KEY', '')
print(f"密钥是否存在: {bool(api_key)}")

if not api_key:
    print("错误：没有找到DeepSeek密钥")
    signal = {
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
        url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=100"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            raise ValueError("币安API返回空数据")
        
        close_prices = [float(c[4]) for c in data]
        df = pd.DataFrame({'close': close_prices})
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        
        current_price = df['close'].iloc[-1]
        rsi_value = df['rsi'].iloc[-1]
        
        # 正确的NaN检查
        if pd.isna(rsi_value) or math.isnan(rsi_value):
            rsi_value = 50
        
        print(f"价格: {current_price}, RSI: {rsi_value}")

        print("正在调用DeepSeek AI...")
        prompt = f"比特币当前价格{current_price:.2f}美元，14周期RSI为{rsi_value:.1f}。请给出买入、卖出或持有建议，输出JSON格式: {{\"操作\":\"买入/卖出/持有\", \"置信度\":0-100, \"理由\":\"简要分析\"}}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }
        
        api_response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        api_response.raise_for_status()
        result = api_response.json()
        
        # 安全的JSON解析
        try:
            ai_reply = json.loads(result["choices"][0]["message"]["content"])
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"AI回复解析失败: {e}")
            ai_reply = {"操作": "持有", "置信度": 50, "理由": "AI响应解析失败"}
        
        signal = {
            '价格': round(current_price, 2),
            'RSI': round(rsi_value, 1),
            '操作': ai_reply.get('操作', '持有'),
            '置信度': int(ai_reply.get('置信度', 50)),
            '理由': ai_reply.get('理由', '无'),
            '更新时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        print("AI调用成功")
        
    except requests.exceptions.Timeout:
        print("错误: 请求超时")
        signal = {
            '价格': 0,
            'RSI': 0,
            '操作': '错误',
            '置信度': 0,
            '理由': '网络请求超时',
            '更新时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except requests.exceptions.RequestException as e:
        print(f"网络错误: {e}")
        signal = {
            '价格': 0,
            'RSI': 0,
            '操作': '错误',
            '置信度': 0,
            '理由': f'网络错误: {type(e).__name__}',
            '更新时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        print(f"发生错误: {e}")
        signal = {
            '价格': 0,
            'RSI': 0,
            '操作': '错误',
            '置信度': 0,
            '理由': f'程序出错: {type(e).__name__}',
            '更新时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

# 生成HTML文件
html_content = f'''<!DOCTYPE html>
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
.action{{font-size:2em;margin:20px;padding:15px;border-radius:40px;font-weight:bold;}}
.买入{{background-color:#2e7d32;color:white;}}
.卖出{{background-color:#c62828;color:white;}}
.持有{{background-color:#ff8f00;color:white;}}
.error{{background-color:#555;color:white;}}
.reason{{background:#00000066;padding:10px;border-radius:12px;margin:15px 0;}}
.time{{font-size:0.8em;color:#aaa;}}
.confidence{{font-size:1.2em;color:#4dd0e1;margin:10px 0;}}
</style>
</head>
<body>
<div class="card">
<h1>🤖 AI实时量化信号</h1>
<div class="price">💰 价格: ${signal['价格']}</div>
<div class="rsi">📊 RSI: {signal['RSI']}</div>
<div class="action {signal['操作']}">📈 操作: {signal['操作']}</div>
<div class="confidence">🎯 置信度: {signal['置信度']}%</div>
<div class="reason">💡 理由: {signal['理由']}</div>
<div class="time">🕒 更新时间: {signal['更新时间']}</div>
</div>
<div class="card"><small>每小时自动更新 | 数据: 币安 | AI: DeepSeek</small></div>
</body>
</html>'''

# 创建输出目录
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
os.makedirs(output_dir, exist_ok=True)

output_file = os.path.join(output_dir, 'index.html')
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"网页文件已生成: {output_file}")

# 同时输出JSON格式的信号数据
signal_file = os.path.join(output_dir, 'signal.json')
with open(signal_file, 'w', encoding='utf-8') as f:
    json.dump(signal, f, ensure_ascii=False, indent=2)

print(f"信号数据已保存: {signal_file}")
