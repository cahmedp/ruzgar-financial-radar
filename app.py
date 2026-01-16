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

@st.cache_data(ttl=300)  # تخزين مؤقت لمدة 5 دقائق
def get_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        current = info.get('regularMarketPrice', info.get('currentPrice', 0))
        volume = info.get('volume') or info.get('regularMarketVolume') or 0
        
        if volume == 0:
            hist_today = ticker.history(period="1d")
            if not hist_today.empty:
                volume = hist_today['Volume'].iloc[-1]
        
        avg_volume = info.get('averageVolume') or 1
        rel_volume = round(volume / avg_volume, 2) if avg_volume > 0 else 'N/A'
        
        high52 = info.get('fiftyTwoWeekHigh', current)
        perc_from_high = round((current / high52 * 100), 1) if high52 > 0 else 'N/A'
        
        rsi = 'N/A'
        hist = ticker.history(period="1mo")
        if not hist.empty:
            delta = hist['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            rsi_val = 100 - (100 / (1 + rs.iloc[-1])) if rs.iloc[-1] != 0 else 50
            rsi = round(rsi_val, 1)
        
        return {
            'Symbol': symbol,
            'Price': round(current, 2),
            'Change %': round(info.get('regularMarketChangePercent', 0) * 100, 2),
            'Rel Volume': rel_volume,
            'Volume': volume,
            'Avg Vol': avg_volume,
            'Market Cap (M)': round(info.get('marketCap', 0) / 1e6, 1) if info.get('marketCap') else 'N/A',
            'Beta': round(info.get('beta', 'N/A'), 2),
            '% from 52W High': perc_from_high,
            'RSI (14)': rsi,
            'Sector': info.get('sector', 'غير متوفر'),
            'Float (M)': round(info.get('floatShares', 0) / 1e6, 2) if info.get('floatShares') else 'N/A',
            'Short %': round(info.get('shortPercentOfFloat', 0) * 100, 2) if info.get('shortPercentOfFloat') else 'N/A',
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
    
    styled_df = df.style.format({
        'Price': '{:.2f}',
        'Change %': '{:+.2f}%',
        'Rel Volume': '{:.2f}x' if isinstance(df['Rel Volume'].iloc[0], (int, float)) else '{}',
        'Volume': '{:,}',
        'Avg Vol': '{:,}',
        'Market Cap (M)': '{:,.1f} M',
        'Beta': '{:.2f}',
        '% from 52W High': '{:.1f}%',
        'RSI (14)': '{:.1f}' if pd.notna(df['RSI (14)'].iloc[0]) else 'N/A',
        'Short %': '{:.2f}%'
    }).background_gradient(subset=['Change %'], cmap='RdYlGn') \
      .background_gradient(subset=['RSI (14)'], cmap='RdYlGn', vmin=30, vmax=70) \
      .background_gradient(subset=['% from 52W High'], cmap='YlGn_r', vmin=0, vmax=100)
    
    st.subheader("جدول المتابعة المتقدم")
    st.dataframe(styled_df, use_container_width=True, height=650)
    
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
    
    st.info("ملاحظة: Relative Volume قد يظهر N/A بسبب قيود yfinance. استخدم مصادر متعددة للتحقق.")
else:
    st.error("تعذر جلب أي بيانات. تحقق من الاتصال أو الرموز.")

st.caption("للأغراض التعليمية فقط | غير مسؤول عن قرارات استثمارية")
