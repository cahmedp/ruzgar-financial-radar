import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
import requests

st.set_page_config(page_title="RUZGAR Financial Radar", page_icon="📈", layout="wide")

# عنوان التطبيق
st.title("📊 RUZGAR Financial Radar - Critical Minerals & Penny Stocks")
st.markdown("**متابعة متقدمة لأسهم المعادن الحرجة و Penny Stocks** | يناير 2026")

# قائمة الأسهم
stocks = [
    'CRML', 'AREC', 'UAMY', 'UUUU', 'TMC', 'NB', 'TMQ', 'IDR', 'PPTA', 'MP', 'ERO',
    'LAC', 'ZENA', 'SGML', 'ABAT','ASTS', 'RKLB', 'HIMS', 'QS', 'NBIS', 'SOFI', 'GRAB', 'TE', 'HOOD',
    'NU', 'CLOV', 'ZETA', 'DLO', 'TSLA', 'PLTR', 'PGY', 'RIVN', 'SRTA', 'IREN', 'RDW', 'MAXQ', 'PNGAY',
    'NXPI'
]

# مفتاح Alpha Vantage (يفضل نقله لاحقًا إلى st.secrets)
API_KEY = "U2X2WAT360XR627R"

@st.cache_data(ttl=300)  # كاش لمدة 5 دقائق
def get_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # ── حساب Change % بطريقة أكثر موثوقية ───────────────────────────────
        hist = ticker.history(period="5d", interval="1d")
        
        if len(hist) >= 2:
            prev_close = float(hist['Close'].iloc[-2])
            current_price = float(hist['Close'].iloc[-1])
            
            # إذا كان آخر يوم تداول اليوم → نحاول نأخذ السعر الحالي إن وجد
            if hist.index[-1].date() == datetime.now().date():
                current_price = info.get('regularMarketPrice') or \
                               info.get('currentPrice') or \
                               current_price
            
            change_pct = ((current_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0.0
        else:
            change_pct = 0.0
            current_price = info.get('regularMarketPrice') or info.get('currentPrice') or 0.0

        # الحجم
        volume = int(hist['Volume'].iloc[-1]) if not hist.empty else 0
        
        avg_volume = info.get('averageVolume10days') or \
                     info.get('averageVolume') or 1
        
        rel_volume = volume / avg_volume if avg_volume > 0 else float('nan')

        # باقي البيانات
        high52 = info.get('fiftyTwoWeekHigh', current_price) or current_price
        perc_from_high = (current_price / high52 * 100) if high52 > 0 else float('nan')

        rsi = float('nan')
        try:
            hist_rsi = ticker.history(period="1mo")
            if not hist_rsi.empty:
                delta = hist_rsi['Close'].diff()
                gain = delta.where(delta > 0, 0).rolling(window=14).mean()
                loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
                rs = gain / loss
                rsi_val = 100 - (100 / (1 + rs.iloc[-1])) if rs.iloc[-1] != 0 else 50
                rsi = float(rsi_val)
        except:
            pass

        # عدد الأخبار
        news_count = 0
        try:
            news_url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&apikey={API_KEY}"
            news_response = requests.get(news_url, timeout=10)
            news_data = news_response.json()
            news_count = len(news_data.get('feed', []))
        except:
            pass

        return {
            'Symbol': symbol,
            'Price': current_price,
            'Change %': change_pct,
            'Rel Volume': rel_volume,
            'Volume': volume,
            'Avg Vol': avg_volume,
            'Market Cap (M)': info.get('marketCap', 0) / 1e6 if info.get('marketCap') else float('nan'),
            'Beta': info.get('beta', float('nan')),
            '% from 52W High': perc_from_high,
            'RSI (14)': rsi,
            'Sector': info.get('sector', 'غير متوفر'),
            'Float (M)': info.get('floatShares', 0) / 1e6 if info.get('floatShares') else float('nan'),
            'Short %': info.get('shortPercentOfFloat', 0) * 100 if info.get('shortPercentOfFloat') else float('nan'),
            'News Count': news_count
        }

    except Exception as e:
        st.warning(f"خطأ في {symbol}: {str(e)}")
        return None

# جمع البيانات
data = []
progress_bar = st.progress(0)
status_text = st.empty()

for i, symbol in enumerate(stocks):
    stock_data = get_stock_data(symbol)
    if stock_data:
        data.append(stock_data)
    
    status_text.text(f"جاري تحميل {symbol} ({i+1}/{len(stocks)})")
    progress_bar.progress((i + 1) / len(stocks))

progress_bar.empty()
status_text.success("تم تحميل البيانات بنجاح!")

# زر التحديث
if st.button("🔄 تحديث البيانات الآن"):
    st.cache_data.clear()
    st.rerun()

if data:
    df = pd.DataFrame(data).sort_values('Change %', ascending=False)
    
    # تحويل الأعمدة الرقمية
    numeric_cols = ['Price', 'Change %', 'Rel Volume', 'Volume', 'Avg Vol', 'Market Cap (M)', 'Beta',
                    '% from 52W High', 'RSI (14)', 'Float (M)', 'Short %', 'News Count']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # فلتر تفاعلي
    st.subheader("فلتر الجدول")
    col1, col2, col3 = st.columns(3)
    
    min_change = col1.slider("أدنى تغيير %", -2000.0, 2000.0, -100.0, step=50.0)
    min_rsi = col2.slider("أدنى RSI", 0.0, 100.0, 30.0, step=5.0)
    min_news = col3.slider("أدنى عدد أخبار", 0, 20, 0)
    
    filtered_df = df[
        (df['Change %'] >= min_change) &
        (df['RSI (14)'].fillna(0) >= min_rsi) &
        (df['News Count'].fillna(0) >= min_news)
    ]
    
    # تنسيق الجدول
    styled_df = filtered_df.style.format(na_rep='N/A').format({
        'Price': '{:.4f}',
        'Change %': '{:+.2f}%',
        'Rel Volume': '{:.2f}x',
        'Volume': '{:,.0f}',
        'Avg Vol': '{:,.0f}',
        'Market Cap (M)': '{:,.1f} M',
        'Beta': '{:.2f}',
        '% from 52W High': '{:.1f}%',
        'RSI (14)': '{:.1f}',
        'Short %': '{:.2f}%',
        'News Count': '{:.0f}'
    })
    
    st.subheader("جدول المتابعة المتقدم")
    st.dataframe(styled_df, use_container_width=True)
    
    # الرسوم البيانية
    col1, col2 = st.columns(2)
    
    with col1:
        fig_change = px.bar(filtered_df, x='Symbol', y='Change %', color='Change %',
                           color_continuous_scale='RdYlGn',
                           title='تغيير الأسعار اليومي (%)')
        fig_change.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_change, use_container_width=True)
    
    with col2:
        fig_rsi = px.bar(filtered_df, x='Symbol', y='RSI (14)', color='RSI (14)',
                         color_continuous_scale='RdYlGn',
                         title='مؤشر القوة النسبية RSI (14)')
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
        fig_rsi.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_rsi, use_container_width=True)
    
    st.success(f"آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | الأسهم المعروضة: {len(filtered_df)} من {len(df)}")
    
    st.info("ملاحظة: بعض الأسهم قد تظهر N/A بسبب عدم توفر البيانات. استخدم الفلتر للتركيز على النتائج الأفضل.")
else:
    st.error("تعذر جلب أي بيانات. تحقق من الاتصال أو الرموز.")

st.caption("للأغراض التعليمية فقط | غير مسؤول عن قرارات استثمارية")
