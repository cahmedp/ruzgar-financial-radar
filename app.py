import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="RUZGAR Financial Radar", page_icon="📈", layout="wide")

st.title("📊 RUZGAR Financial Radar - Critical Minerals & Penny Stocks")
st.markdown("**متابعة متقدمة لأسهم المعادن الحرجة و Penny Stocks** | يناير 2026")

stocks = [
    'CRML', 'AREC', 'UAMY', 'UUUU', 'TMC', 'NB', 'TMQ', 'IDR', 'PPTA', 'MP', 'ERO',
    'LAC', 'LICY', 'SGML', 'ABAT'
]

@st.cache_data(ttl=300)
def get_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        current = info.get('regularMarketPrice', info.get('currentPrice', 0)) or 0
        volume = info.get('volume') or info.get('regularMarketVolume') or 0
        
        if volume == 0:
            hist_today = ticker.history(period="1d")
            if not hist_today.empty:
                volume = hist_today['Volume'].iloc[-1]
        
        avg_volume = info.get('averageVolume') or 1
        rel_volume = volume / avg_volume if avg_volume > 0 else float('nan')
        
        high52 = info.get('fiftyTwoWeekHigh', current) or current
        perc_from_high = (current / high52 * 100) if high52 > 0 else float('nan')
        
        rsi = float('nan')
        try:
            hist = ticker.history(period="1mo")
            if not hist.empty:
                delta = hist['Close'].diff()
                gain = delta.where(delta > 0, 0).rolling(window=14).mean()
                loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
                rs = gain / loss
                rsi_val = 100 - (100 / (1 + rs.iloc[-1])) if rs.iloc[-1] != 0 else 50
                rsi = rsi_val
        except:
            pass
        
        return {
            'Symbol': symbol,
            'Price': current,
            'Change %': info.get('regularMarketChangePercent', 0) * 100,
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
        }
    except Exception as e:
        st.warning(f"خطأ في {symbol}: {str(e)}")
        return None

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

if data:
    df = pd.DataFrame(data).sort_values('Change %', ascending=False)
    
    # تحويل الأعمدة الرقمية لتجنب مشاكل التنسيق
    numeric_cols = ['Price', 'Change %', 'Rel Volume', 'Volume', 'Avg Vol', 'Market Cap (M)', 'Beta',
                    '% from 52W High', 'RSI (14)', 'Float (M)', 'Short %']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # تنسيق بسيط بدون gradient على أعمدة قد تكون NaN
    styled_df = df.style.format(na_rep='N/A').format({
        'Price': '{:.2f}',
        'Change %': '{:+.2f}%',
        'Rel Volume': '{:.2f}x',
        'Volume': '{:,.0f}',
        'Avg Vol': '{:,.0f}',
        'Market Cap (M)': '{:,.1f} M',
        'Beta': '{:.2f}',
        '% from 52W High': '{:.1f}%',
        'RSI (14)': '{:.1f}',
        'Short %': '{:.2f}%'
    })
    
    st.subheader("جدول المتابعة المتقدم")
    # عرض الجدول بدون height أولاً لتجنب الخطأ
    st.dataframe(styled_df, use_container_width=True)
    
    # إضافة gradient بعد العرض الأساسي (اختياري)
    try:
        st.markdown("**تدرج الألوان للتغيير والـ RSI**")
        st.dataframe(
            df.style.background_gradient(subset=['Change %'], cmap='RdYlGn')
                    .background_gradient(subset=['RSI (14)'], cmap='RdYlGn', vmin=30, vmax=70),
            use_container_width=True
        )
    except:
        st.info("التدرج اللوني غير متاح حاليًا بسبب بعض القيم الفارغة.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_change = px.bar(df, x='Symbol', y='Change %', color='Change %',
                           color_continuous_scale='RdYlGn',
                           title='تغيير الأسعار اليومي (%)')
        fig_change.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_change, use_container_width=True)
    
    with col2:
        fig_rsi = px.bar(df, x='Symbol', y='RSI (14)', color='RSI (14)',
                         color_continuous_scale='RdYlGn',
                         title='مؤشر القوة النسبية RSI (14)')
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
        fig_rsi.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_rsi, use_container_width=True)
    
    st.success(f"آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | الأسهم الناجحة: {len(df)}")
    
    st.info("ملاحظة: بعض الأسهم قد تظهر N/A بسبب عدم توفر البيانات من yfinance.")
else:
    st.error("تعذر جلب أي بيانات. تحقق من الاتصال أو الرموز.")

st.caption("للأغراض التعليمية فقط | غير مسؤول عن قرارات استثمارية")
