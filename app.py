import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import requests
import json

st.set_page_config(page_title="RUZGAR Financial Radar", page_icon="📈", layout="wide")

st.title("📊 RUZGAR Financial Radar - Critical Minerals & Penny Stocks")
st.markdown("**متابعة متقدمة لأسهم المعادن الحرجة و Penny Stocks** | يناير 2026")

API_KEY = "U2X2WAT360XR627R"  # API key for Alpha Vantage

stocks = [
    'CRML', 'AREC', 'UAMY', 'UUUU', 'TMC', 'NB', 'TMQ', 'IDR', 'PPTA', 'MP', 'ERO',
    'LAC', 'LICY', 'SGML', 'ABAT'
]

data = []
progress_bar = st.progress(0)
status_text = st.empty()

def get_alpha_vantage_data(symbol):
    try:
        # Fetch daily time series for price, change, volume
        url_daily = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"
        response_daily = requests.get(url_daily)
        data_daily = response_daily.json()
        
        if "Time Series (Daily)" not in data_daily:
            raise ValueError("No daily data available")
        
        daily_series = data_daily["Time Series (Daily)"]
        latest_date = max(daily_series.keys())
        latest = daily_series[latest_date]
        prev_date = sorted(daily_series.keys())[-2]
        prev = daily_series[prev_date]
        
        current = float(latest['4. close'])
        prev_close = float(prev['4. close'])
        change_perc = round(((current - prev_close) / prev_close) * 100, 2)
        volume = int(latest['5. volume'])
        
        # Fetch global quote for average volume approximation (use 10-day if available, else estimate)
        url_global = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
        response_global = requests.get(url_global)
        data_global = response_global.json()["Global Quote"]
        
        avg_volume = int(data_global.get('10. volume', volume))  # Fallback to today's volume if not available
        
        rel_volume = round(volume / avg_volume, 2) if avg_volume > 0 else 'N/A'
        
        # Fetch overview for market cap, beta, sector
        url_overview = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={API_KEY}"
        response_overview = requests.get(url_overview)
        overview = response_overview.json()
        
        market_cap = overview.get('MarketCapitalization', 'N/A')
        if market_cap != 'N/A':
            market_cap = round(int(market_cap) / 1e6, 1)
        
        beta = round(float(overview.get('Beta', 'N/A')), 2)
        sector = overview.get('Sector', 'غير متوفر')
        
        # 52-week high/low from overview
        high52 = float(overview.get('52WeekHigh', current))
        perc_from_high = round((current / high52 * 100), 1) if high52 > 0 else 'N/A'
        
        # RSI from Alpha Vantage
        url_rsi = f"https://www.alphavantage.co/query?function=RSI&symbol={symbol}&interval=daily&time_period=14&series_type=close&apikey={API_KEY}"
        response_rsi = requests.get(url_rsi)
        rsi_data = response_rsi.json().get("Technical Analysis: RSI", {})
        rsi = 'N/A'
        if rsi_data:
            latest_rsi_date = max(rsi_data.keys())
            rsi = round(float(rsi_data[latest_rsi_date]['RSI']), 1)
        
        # Short % and Float approximation (Alpha Vantage doesn't have direct, fallback to overview or N/A)
        short_perc = overview.get('ShortRatio', 'N/A')  # Approximate
        float_m = overview.get('SharesFloat', 'N/A')
        if float_m != 'N/A':
            float_m = round(int(float_m) / 1e6, 2)
        
        return {
            'Symbol': symbol,
            'Price': round(current, 2),
            'Change %': change_perc,
            'Rel Volume': rel_volume,
            'Volume': volume,
            'Avg Vol': avg_volume,
            'Market Cap (M)': market_cap,
            'Beta': beta,
            '% from 52W High': perc_from_high,
            'RSI (14)': rsi,
            'Sector': sector,
            'Float (M)': float_m,
            'Short %': short_perc,
        }
    
    except Exception as e:
        st.warning(f"خطأ في {symbol}: {str(e)}")
        return None

for i, symbol in enumerate(stocks):
    stock_data = get_alpha_vantage_data(symbol)
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
        'Market Cap (M)': '{:,.1f} M' if isinstance(df['Market Cap (M)'].iloc[0], (int, float)) else '{}',
        'Beta': '{:.2f}',
        '% from 52W High': '{:.1f}%',
        'RSI (14)': '{:.1f}' if pd.notna(df['RSI (14)'].iloc[0]) else 'N/A',
        'Short %': '{:.2f}%' if isinstance(df['Short %'].iloc[0], (int, float)) else '{}'
    }).background_gradient(
        subset=['Change %'],
        cmap='RdYlGn'
    ).background_gradient(
        subset=['RSI (14)'],
        cmap='RdYlGn',
        vmin=30, vmax=70
    ).background_gradient(
        subset=['% from 52W High'],
        cmap='YlGn_r',
        vmin=0, vmax=100
    )
    
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
    
    st.info("ملاحظة: البيانات من Alpha Vantage. قد يكون هناك تأخير في بعض البيانات.")
else:
    st.error("تعذر جلب أي بيانات. تحقق من الاتصال أو الرموز.")

st.caption("للأغراض التعليمية والبحثية فقط | غير مسؤول عن قرارات استثمارية")
