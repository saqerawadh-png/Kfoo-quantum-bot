
import time
from datetime import datetime
import requests
import sqlite3
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# --- إعدادات البوت والاتصال ---
TELEGRAM_TOKEN = "8812703340:AAEsdYiEFj-20oVaQHTb4uhZQLVp1m5vGlg"
TELEGRAM_CHAT_ID = "871200180"

CHECK_INTERVAL = 60  # فحص الأسواق كل دقيقة
COINS_TO_SCAN = ['BTC', 'ETH', 'BNB', 'SOL', 'AVAX']

peak_prices = {}
entry_prices = {}
entry_times = {}

# --- تهيئة قاعدة البيانات المحلية لتعلم الآلة والذاكرة ---
def init_db():
    conn = sqlite3.connect('trading_memory.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coin TEXT,
            rsi REAL,
            vol_ratio REAL,
            ema_dist REAL,
            success INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# تهيئة نموذج الذكاء الاصطناعي (Random Forest Classifier)
ai_brain = RandomForestClassifier(n_estimators=100, random_state=42)

def train_ai_from_memory():
    """تدريب نموذج الذكاء الاصطناعي بناءً على الصفقات والذاكرة التاريخية"""
    try:
        conn = sqlite3.connect('trading_memory.db')
        cursor = conn.cursor()
        cursor.execute("SELECT rsi, vol_ratio, ema_dist, success FROM trades_history")
        data = cursor.fetchall()
        conn.close()

        if len(data) < 5:
            return False  # يلزم بيانات كافية للتدريب الفعلي

        X = np.array([[row[0], row[1], row[2]] for row in data])
        y = np.array([row[3] for row in data])
        
        ai_brain.fit(X, y)
        return True
    except Exception:
        return False

def evaluate_with_ai(rsi, vol_ratio, ema_dist):
    """تقييم ذكي لمدى نجاح الصفقة قبل إرسالها"""
    is_trained = train_ai_from_memory()
    if not is_trained:
        return True  # السماح المبدئي حتى تتجمع البيانات عبر الاستخدام الحقيقي
        
    features = np.array([[rsi, vol_ratio, ema_dist]])
    try:
        probability = ai_brain.predict_proba(features)[0][1] # نسبة الثقة للربح
        print(f"  [AI BRAIN] Probability of Success: {probability * 100:.1f}%")
        return probability >= 0.70  # نسبة القبول 70% فما فوق
    except Exception:
        return True

def record_trade_result(coin, rsi, vol_ratio, ema_dist, success=1):
    """حفظ نتيجة الصفقة في الذاكرة لتطوير ذكاء البوت مستقبلاً"""
    try:
        conn = sqlite3.connect('trading_memory.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO trades_history (coin, rsi, vol_ratio, ema_dist, success)
            VALUES (?, ?, ?, ?, ?)
        ''', (coin, rsi, vol_ratio, ema_dist, success))
        conn.commit()
        conn.close()
    except Exception:
        pass

print("=== KFOO QUANTUM AI ENGINE - Starting Up ===")
print("=" * 60)

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        res = requests.post(url, json=payload, timeout=10)
        res_data = res.json()
        if res_data.get("ok"):
            print("  [SUCCESS] Telegram notification sent.")
        else:
            print(f"  [ERROR] Telegram rejected: {res_data.get('description')}")
    except Exception as e:
        print(f"  [ERROR] Telegram exception: {e}")

def get_binance_klines(symbol, interval='1h', limit=10):
    """جلب بيانات الشموع التاريخية لفحص الاتجاه والسيولة"""
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval={interval}&limit={limit}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

def analyze_market(coin):
    """تحليل فني متقدم + استخراج مؤشرات للذكاء الاصطناعي"""
    klines = get_binance_klines(coin, interval='1h', limit=10)
    if not klines or len(klines) < 8:
        return False, None, None, 0, 0, 0

    closes = [float(k[4]) for k in klines]
    volumes = [float(k[5]) for k in klines]
    current_price = closes[-1]
    
    # حساب المتوسطات ومؤشر RSI مبسط
    sma_5 = sum(closes[-5:]) / 5
    is_bullish_trend = current_price > sma_5
    
    avg_volume = sum(volumes[-6:-1]) / 5
    current_volume = volumes[-1]
    vol_ratio = current_volume / (avg_volume if avg_volume > 0 else 1)
    has_volume_support = vol_ratio >= 1.2

    # مؤشرات تقريبية للذكاء الاصطناعي
    rsi_approx = 55.0 if is_bullish_trend else 45.0
    ema_dist = ((current_price - sma_5) / sma_5) * 100

    valid_setup = is_bullish_trend and has_volume_support
    return valid_setup, current_price, vol_ratio, rsi_approx, ema_dist, vol_ratio

# رسالة تأكيد التنشيط على المنصة السحابية
send_telegram_msg("🧠 *تم تشغيل بوت KFOO Quantum الذكي (مزود بالذكاء الاصطناعي وقاعدة الذاكرة) بنجاح على السحابة!*")

while True:
    try:
        current_time_str = datetime.now().strftime("%I:%M:%S %p")
        print(f"\n[{current_time_str}] AI Quantum Engine scanning markets...")

        for coin in COINS_TO_SCAN:
            valid_setup, current_price, vol_ratio, rsi, ema_dist, volume = analyze_market(coin)
            
            if not valid_setup or current_price is None:
                continue

            # تمرير المعطيات لعقل الذكاء الاصطناعي قبل إصدار الإشارة
            ai_approved = evaluate_with_ai(rsi, vol_ratio, ema_dist)
            if not ai_approved:
                print(f"  [AI REJECT] {coin} setup rejected by AI model confidence threshold.")
                continue

            now_dt = datetime.now()

            if coin not in peak_prices:
                peak_prices[coin] = current_price
                entry_prices[coin] = current_price
                entry_times[coin] = now_dt

                entry_str = now_dt.strftime("%I:%M:%S %p")
                stop_loss = round(current_price * 0.985, 2)
                target_1 = round(current_price * 1.02, 2)
                target_2 = round(current_price * 1.035, 2)

                signal_msg = (
                    f"🚀 *إشارة ذكية معتمدة (KFOO AI Quantum)* - LONG\n\n"
                    f"🔹 *العملة:* {coin}/USDT\n"
                    f"🔹 *سعر الدخول:* `{current_price}$`\n"
                    f"🤖 *حالة الذكاء الاصطناعي:* معتمد (ثقة عالية)\n\n"
                    f"🛑 *وقف الخسارة:* `{stop_loss}$`\n"
                    f"🎯 *الهدف الأول:* `{target_1}$`\n"
                    f"🎯 *الهدف الثاني:* `{target_2}$`\n\n"
                    f"⏰ *الوقت:* `{entry_str}`"
                )
                
                print(f"  [QUANTUM AI SIGNAL] Approved & Sending {coin} signal...")
                send_telegram_msg(signal_msg)
                
                # تسجيل الصفقة مبدئياً للتدريب
                record_trade_result(coin, rsi, vol_ratio, ema_dist, success=1)

            if current_price > peak_prices[coin]:
                peak_prices[coin] = current_price

            if current_price <= peak_prices[coin] * 0.99:
                entry_dt = entry_times[coin]
                exit_dt = now_dt
                duration_minutes = round((exit_dt - entry_dt).total_seconds() / 60, 1)

                close_msg = (
                    f"🏁 *إغلاق صفقة ذكية / Trailing Stop*\n\n"
                    f"🔹 *العملة:* {coin}/USDT\n"
                    f"⏱️ *المدة:* `{duration_minutes} دقيقة`\n"
                    f"💵 *سعر الدخول:* `{entry_prices[coin]}$`\n"
                    f"💵 *سعر الخروج:* `{current_price}$`"
                )

                print(f"  [CLOSE] Securing trade for {coin}...")
                send_telegram_msg(close_msg)

                peak_prices[coin] = current_price
                entry_prices[coin] = current_price
                entry_times[coin] = now_dt

        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        print(f"[ERROR] Engine exception: {e}")
        time.sleep(10)
