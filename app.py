import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import json
from PIL import Image
import requests

# --- 1. 初始化 Google Sheets ---
def init_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_info = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    return gspread.authorize(creds)

# --- 初始化 Gemini ---
def init_gemini(api_key):
    genai.configure(api_key=api_key)
    # 嘗試使用最標準的名稱，如果 flash 不行，也可以試試 gemini-pro
    return genai.GenerativeModel('models/gemini-2.5-flash')

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
model = init_gemini(GEMINI_API_KEY)

def get_ai_advice(spot_name, country):
    prompt = f"我正在規劃去 {country} 旅遊，景點是 {spot_name}。請提供 50 字以內的簡短介紹與建議 像是一定要點那些餐點 看那些東西等等。"
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"暫時無法獲取建議：{e}"


# 幣值映射表
CURRENCY_MAP = {"日本 (Japan)": "JPY", "美國 (USA)": "USD", "韓國 (South Korea)": "KRW", "台灣 (Taiwan)": "TWD", "泰國 (Thailand)": "THB"}

# AI 辨識收據功能
def analyze_receipt(image_file):
    if image_file:
        model = genai.GenerativeModel('gemini-1.5-flash') # 使用 flash 處理圖片速度快且便宜
        img = Image.open(image_file)
        prompt = "請分析這張收據，並以 JSON 格式回傳：{'item': '項目名稱', 'amount': 數字金額, 'category': '交通/住宿/飲食/購物/其他'}"
        response = model.generate_content([prompt, img])
        # ... 解析 JSON 邏輯 (同先前解析航班) ...

def get_travel_time(origin, destination, country):
    GOOGLE_MAPS_API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
    
    # 為了準確性，搜尋時加入國家名稱
    origin_query = f"{country} {origin}"
    dest_query = f"{country} {destination}"
    
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin_query,
        "destinations": dest_query,
        "mode": "transit", # 設定為大眾運輸
        "language": "zh-TW",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(url, params=params).json()
        if response['status'] == 'OK':
            element = response['rows'][0]['elements'][0]
            if element['status'] == 'OK':
                duration = element['duration']['text'] # 例如: "25 分鐘"
                distance = element['distance']['text'] # 例如: "5.2 公里"
                return f"{duration} ({distance})"
        return "無法計算交通 (請檢查地點名稱)"
    except:
        return "計算超時"


client = init_gspread()
SHEET_ID = "19xCUkRCOw5gdTPNPNWyhX2KOz88JjjmT1Nl3EFHLMIw" 
spreadsheet = client.open_by_key(SHEET_ID)

try:
    index_ws = spreadsheet.worksheet("Index")
except:
    # 這裡定義你要求的所有結構化欄位
    headers = [
        "名稱", "開始日期", "結束日期", "國家", 
        "航班號", "出發機場", "出發時間", "抵達機場", "抵達時間",
        "酒店名稱", "酒店地址", "入住日期", "退房日期"
    ]
    index_ws = spreadsheet.add_worksheet(title="Index", rows="100", cols=len(headers))
    index_ws.append_row(headers)

# @st.cache_data(ttl=3600)


# 國家建議清單
country_list = ["日本 (Japan)", "美國 (USA)", "韓國 (South Korea)", "台灣 (Taiwan)", "泰國 (Thailand)"]

# --- 2. 網頁介面設定 ---
st.set_page_config(page_title="Jay Travel Planner", layout="wide")

# --- 插入自定義 CSS ---
st.markdown("""
<style>
/* ===== 全域基礎設定 ===== */
:root {
    --bg: #F7F7F5;
    --panel: #FFFFFF;
    --border: rgba(55, 53, 47, 0.15);
    --text-main: #191919; /* 強制深黑色，確保可見 */
    --text-muted: #666666;
    --accent: #2383E2;
    --radius: 12px;
}

/* 強制所有基本文字顯示顏色 */
.stApp {
    background: var(--bg);
    color: var(--text-main) !important;
}

/* 針對 Streamlit 標題與文字的強制修正 */
h1, h2, h3, h4, h5, p, span, label {
    color: var(--text-main) !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
}

/* ===== 主內容區優化 ===== */
section.main > div {
    max-width: 900px;
    padding: 1rem 0.8rem !important;
}

/* ===== 解決手機版 Tabs 顏色問題 ===== */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    overflow-x: auto;
    flex-wrap: nowrap;
    scrollbar-width: none;
}
.stTabs [data-baseweb="tab"] {
    height: 40px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 0 16px;
    color: var(--text-main) !important;
}
/* 選中的標籤變深色，文字變白色 */
.stTabs [aria-selected="true"] {
    background: var(--text-main) !important;
    border-color: var(--text-main) !important;
}
.stTabs [aria-selected="true"] p {
    color: #FFFFFF !important;
}

/* ===== 行程卡片 (Itinerary Cards) ===== */
div[data-testid="stVerticalBlock"] > div[style*="border"] {
    background: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 18px !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.03) !important;
    margin-bottom: 12px !important;
}

/* ===== 按鈕優化 (大面積觸控) ===== */
.stButton > button {
    width: 100%;
    height: 3.5rem !important;
    border-radius: 14px;
    border: 1px solid var(--border);
    background: var(--panel);
    color: var(--text-main) !important;
    font-weight: 600;
    font-size: 1rem;
    margin-top: 5px;
}

/* 黑色主要按鈕 (如：記帳、確認) */
.stButton > button[kind="primary"] {
    background: var(--text-main) !important;
    color: #FFFFFF !important;
    border: none;
}

/* ===== 側邊欄文字修正 ===== */
section[data-testid="stSidebar"] .stMarkdown, 
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p {
    color: var(--text-main) !important;
}

/* ===== 手機版微調 ===== */
@media (max-width: 640px) {
    h1 { font-size: 1.8rem !important; margin-bottom: 0.5rem !important; }
    /* 讓兩欄排版在極小螢幕不要縮得太擠 */
    div[data-testid="column"] {
        min-width: 45% !important;
    }
}
</style>
""", unsafe_allow_html=True)

# --- 3. 左側 Panel: 歷史旅程清單與建立旅程 ---
with st.sidebar:
    st.title("🗂️ 旅程管理")
    
    # 功能 1: 顯示所有歷史旅程 (排除預設的 Sheet1)
    all_sheets = [s.title for s in spreadsheet.worksheets() if s.title != "Sheet1"]
    
    st.subheader("📜 歷史旅程")
    if all_sheets:
        # 使用 radio 或 selectbox 讓用戶選擇現有行程
        selected_trip = st.radio("選取旅程切換內容：", all_sheets)
    else:
        st.info("尚無存檔旅程")
        selected_trip = None

    st.divider()

    # 功能 2: 建立新旅程 (唯一可以編輯日期與國家的地方)
    st.subheader("➕ 開啟新旅程")
    with st.expander("填寫新旅程基本資訊"):
        new_name = st.text_input("旅程名稱 (例如: 東京2025)")
        c1, c2 = st.columns(2)
        with c1:
            new_start = st.date_input("出發日期")
        with c2:
            new_end = st.date_input("結束日期")
        new_country = st.selectbox("選擇國家", options=country_list)
        total_days = (new_end - new_start).days + 1
        if st.button("確認建立新旅程"):
            if new_name and new_name not in all_sheets:
                new_ws = spreadsheet.add_worksheet(title=new_name, rows="100", cols="6")
                # 標題要跟後面的 df 呼叫名稱完全一致
                new_ws.append_row(["日期", "開始時間", "結束時間", "活動", "地圖連結", "備註"]) 

                # Index 表紀錄
                index_ws.append_row([new_name, str(new_start), str(new_end), new_country, "", ""])
                st.success(f"✅ {new_name} 已建立！")
                st.rerun()
            else:
                st.error("請輸入有效且未重複的旅程名稱")

# --- 4. 主畫面: 詳細行程規劃 (Itinerary) ---
if selected_trip:
        
    current_sheet = spreadsheet.worksheet(selected_trip)
    # 1. 抓取 Index 表中的基本資訊
    index_all = index_ws.get_all_values()
    index_df = pd.DataFrame(index_all[1:], columns=index_all[0])
    
    # 找到對應那一列的資料
    this_trip_info = index_df[index_df["名稱"] == selected_trip]
    if not this_trip_info.empty:
        basic_data = this_trip_info.iloc[0].tolist()
    else:
        st.error("找不到該旅程的基本資訊")
        st.stop()

    # 2. 進行日期運算 (basic_data[1]是開始, basic_data[2]是結束)
    # 注意：Index 表的順序是 [名稱, 開始, 結束, 國家, 航班, 酒店]
    from datetime import datetime, timedelta
    start_date_str = basic_data[1]
    end_date_str = basic_data[2]
    country_name = basic_data[3]
    
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    duration = (end_date - start_date).days + 1
    date_range = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(duration)]
    
    st.info(f"📅 期間：{basic_data[1]} ~ {basic_data[2]} | 🌍 國家/天數：{basic_data[3]}/ {duration}天")

    @st.dialog("✈️ 編輯航班資訊")
    def edit_flights(trip_sheet):
        with st.form("flight_form", clear_on_submit=True):
            st.subheader("新增一段航班")
            f_no = st.text_input("航班號 (例如: BR198)")
            col1, col2 = st.columns(2)
            with col1:
                f_dep = st.text_input("出發地/機場")
                f_dep_t = st.text_input("出發時間 (HH:MM)")
            with col2:
                f_arr = st.text_input("目的地/機場")
                f_arr_t = st.text_input("抵達時間 (HH:MM)")
            f_date = st.selectbox("航班日期", options=date_range)
            
            if st.form_submit_button("確認新增航班"):
                if f_no and f_dep_t:
                    # 直接寫入該旅程的行程表
                    trip_sheet.append_row([
                        f_date, f_dep_t, f_arr_t, 
                        f"✈️ 航班: {f_no} ({f_dep} 🛫 {f_arr})", 
                        "", "航班資訊"
                    ])
                    st.success("✅ 航班已加入行程！")
                    st.rerun() # 跳回主畫面

    @st.dialog("🏨 編輯飯店資訊")
    def edit_hotels(trip_sheet):
        with st.form("hotel_form", clear_on_submit=True):
            st.subheader("新增飯店入住紀錄")
            h_name = st.text_input("飯店名稱")
            h_addr = st.text_input("飯店地址")
            col1, col2 = st.columns(2)
            with col1:
                h_in = st.date_input("入住日期")
            with col2:
                h_out = st.date_input("退房日期")
            
            if st.form_submit_button("確認儲存飯店"):
                # 將飯店資訊存入行程
                # 入住日
                trip_sheet.append_row([str(h_in), "15:00", "23:59", f"🏨 入住: {h_name}", "", h_addr])
                # 退房日
                trip_sheet.append_row([str(h_out), "00:00", "11:00", f"🔑 退房: {h_name}", "", ""])
                st.success("✅ 飯店資訊已儲存！")
                st.rerun()

        st.divider()

        # # 第二區：用戶手動校對與編輯
        # st.subheader("📝 核對詳細資訊")
        # col1, col2 = st.columns(2)
        # with col1:
        #     f_no = st.text_input("航班號", value=st.session_state.temp_meta["航班號"])
        #     f_dep = st.text_input("出發機場", value=st.session_state.temp_meta["出發機場"])
        #     f_dep_t = st.text_input("出發時間 (HH:MM)", value=st.session_state.temp_meta["出發時間"])
        #     h_name = st.text_input("酒店名稱", value=st.session_state.temp_meta["酒店名稱"])
        #     h_checkin = st.text_input("入住日期 (YYYY-MM-DD)", value=st.session_state.temp_meta["入住日期"])
        # with col2:
        #     st.write("") # 對齊用
        #     f_arr = st.text_input("抵達機場", value=st.session_state.temp_meta["抵達機場"])
        #     f_arr_t = st.text_input("抵達時間 (HH:MM)", value=st.session_state.temp_meta["抵達時間"])
        #     h_addr = st.text_input("酒店地址", value=st.session_state.temp_meta["酒店地址"])
        #     h_checkout = st.text_input("退房日期 (YYYY-MM-DD)", value=st.session_state.temp_meta["退房日期"])

        # # 儲存按鈕 (不放在 st.form 裡以避免解析問題)
        # if st.button("💾 確認儲存並更新 Index", use_container_width=True, type="primary"):
        #     with st.spinner("儲存中..."):
        #         # 1. 找到 Index 表對應列
        #         cell = index_ws.find(selected_trip)
        #         row = cell.row
                
        #         # 2. 依照順序準備更新值
        #         # 欄位: 航班號(5), 出發機場(6), 出發時間(7), 抵達機場(8), 抵達時間(9), 酒店(10), 地址(11), 入住(12), 退房(13)
        #         update_vals = [f_no, f_dep, f_dep_t, f_arr, f_arr_t, h_name, h_addr, h_checkin, h_checkout]
                
        #         # 執行更新
        #         range_label = f"E{row}:M{row}" # 假設從第五欄(E)到第十三欄(M)
        #         index_ws.update(range_label, [update_vals])
                
        #         # 3. 如果是用戶透過 AI 解析的，詢問是否要順便加入 Day 1 行程 (選配邏輯)
        #         # 這裡為了單純，我們先專注於更新 Index

        #     if f_no and f_dep_t:
        #         day1_date = basic_data[1] # 開始日期
        #         # 檢查是否已存在該航班行程，避免重複寫入
        #         existing_plans = current_sheet.get_all_values()
        #         if not any(f_no in row for row in existing_plans):
        #             current_sheet.append_row([
        #                 day1_date, 
        #                 f_dep_t, 
        #                 f_arr_t if f_arr_t else "23:59", 
        #                 f"✈️ 航班: {f_no} ({f_dep} 🛫 {f_arr})", 
        #                 "", 
        #                 "AI 自動生成：請提前抵達機場"
        #             ])    

        #         del st.session_state.temp_meta # 儲存完畢清除暫存
        #         st.success("Index 更新成功！")
        #         st.rerun()


    st.title(f"📍 {selected_trip}")
    # 5. 在主頁面放置按鈕
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("✈️ 加航班", use_container_width=True):
            edit_flights(current_sheet)
    with c2:
        if st.button("🏨 加飯店", use_container_width=True):
            edit_hotels(current_sheet)
    with c3:
        if st.button("💵 記帳", use_container_width=True, type="primary"):
            add_expense_dialog(selected_trip, country_name)

    
    @st.dialog("💰 新增花費")
    def add_expense_dialog(trip_name, country):
        expense_ws_name = f"{trip_name}_Expenses"
        
        # 檢查或建立記帳表
        try:
            exp_ws = spreadsheet.worksheet(expense_ws_name)
        except:
            exp_ws = spreadsheet.add_worksheet(title=expense_ws_name, rows="100", cols="5")
            exp_ws.append_row(["款項敘述", "類別", "花費", "幣值", "日期"])

        with st.form("expense_form"):
            uploaded_file = st.file_uploader("📸 上傳收據/發票 (AI 自動填入)", type=['png', 'jpg', 'jpeg'])
            # 這裡可加入 AI 解析邏輯...
            
            desc = st.text_input("款項敘述")
            cat = st.selectbox("類別", ["交通", "住宿", "飲食", "購物", "其他"])
            amount = st.number_input("輸入花費", min_value=0.0)
            submitted = st.form_submit_button("確認新增")
            
            # 根據國家預設幣值
            default_curr = CURRENCY_MAP.get(country, "TWD")
            curr = st.selectbox("選擇幣值", ["TWD", "JPY", "USD", "KRW", "THB", "EUR"], index=["TWD", "JPY", "USD", "KRW", "THB", "EUR"].index(default_curr))
            
            if submitted:
                if desc and amount > 0:
                    # 執行寫入 Google Sheets 的動作
                    exp_ws.append_row([desc, "類別", amount, "幣值", "日期"])
                    st.success("✅ 已記錄！")
                    st.rerun()
                else:
                    st.error("請填寫完整資訊")

    def show_expense_summary(trip_name):
        expense_ws_name = f"{trip_name}_Expenses"
        try:
            exp_ws = spreadsheet.worksheet(expense_ws_name)
            data = exp_ws.get_all_values()
            if len(data) > 1:
                df_exp = pd.DataFrame(data[1:], columns=data[0])
                df_exp["花費"] = pd.to_numeric(df_exp["花費"], errors='coerce')
                
                total_cost = df_exp["花費"].sum()
                
                st.metric("💰 旅程總花費", f"{total_cost:,.0f}")
                
                # 顯示各類別佔比
                cat_sum = df_exp.groupby("類別")["花費"].sum()
                cols = st.columns(len(cat_sum))
                for idx, (cat, val) in enumerate(cat_sum.items()):
                    percent = (val / total_cost) * 100
                    cols[idx].caption(f"**{cat}**\n{percent:.0f}%")
            else:
                st.caption("尚無消費記錄")
        except:
            st.caption("尚未建立記帳本")

    

    # 顯示花費統計
    show_expense_summary(selected_trip)

    st.subheader("📅 行程詳情")
    all_values = current_sheet.get_all_values()
    if len(all_values) > 1:
        df = pd.DataFrame(all_values[1:], columns=["日期", "開始時間", "結束時間", "活動", "地圖連結", "備註"])
    else:
        df = pd.DataFrame(columns=["日期", "開始時間", "結束時間", "活動", "地圖連結", "備註"])

    tabs = st.tabs([f"Day {i+1} ({d})" for i, d in enumerate(date_range)])

    for i, date_str in enumerate(date_range):
        with tabs[i]:
            day_items = df[df["日期"] == date_str].copy()
            st.caption(f"📍 本日住宿：{get_today_hotel(date_str, items_list)}")
       
            if not day_items.empty:
                # 確保時間格式正確並排序
                day_items['temp_time'] = pd.to_datetime(day_items['開始時間'], format='%H:%M', errors='coerce')
                day_items = day_items.sort_values(by='temp_time')
                items_list = day_items.to_dict('records')
                
                for idx, row in enumerate(items_list):
                    # 建立行事曆風格的佈局
                    # 左邊 col1 放時間軸，右邊 col2 放活動內容
                    col1, col2 = st.columns([1, 4])
                    
                    with col1:
                        # 顯示開始與結束時間，並加粗
                        st.markdown(f"**{row['開始時間']}**")
                        st.markdown(f"至 {row['結束時間']}")
                        # 視覺上的時間軸線
                        st.markdown("---")
                    
                    with col2:
                        # 使用 container 建立彩色活動塊
                        # 這裡可以根據活動類型手動加上不同顏色（進階功能）
                        with st.container(border=True):
                            # 第一行：活動名稱與連結
                            st.markdown(f"#### 📍 {row['活動']}")
                            
                            # 第二行：備註與 AI 建議
                            if row['備註']:
                                st.markdown(f"*{row['備註']}*")
                            
                            # 按鈕列
                            btn_col1, btn_col2 = st.columns([1, 1])
                            with btn_col1:
                                st.link_button("🗺️ 地圖導航", row['地圖連結'], use_container_width=True)
                            with btn_col2:
                                if st.button("✨ AI 建議", key=f"ai_btn_{date_str}_{idx}", use_container_width=True):
                                    advice = get_ai_advice(row['活動'], country_name)
                                    st.info(advice)

                    # 交通接駁資訊（顯示在兩個活動卡片之間）
                    if idx < len(items_list) - 1:
                        next_row = items_list[idx+1]
                        travel_info = get_travel_time(row['活動'], next_row['活動'], country_name)
                        # 模擬行事曆中的交通小圖示
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 🚌 <small>{travel_info}</small>", unsafe_allow_html=True)
            else:
                st.info("📅 這天還沒有安排行程，點擊下方「添加新景點」開始規劃！")

    # for date_str in date_range:
    #     with st.expander(f"📅 {date_str}", expanded=True):
    #         day_items = df[df["日期"] == date_str].copy() # 建立副本避免報錯
    #         if not day_items.empty:
    #             day_items['temp_time'] = pd.to_datetime(day_items['開始時間'], format='%H:%M', errors='coerce')
    #             day_items = day_items.sort_values(by='temp_time')
                
    #             # 顯示行程與計算交通
    #             items_list = day_items.to_dict('records')
    #             for i, row in enumerate(items_list):
    #                 # 顯示當前行程
    #                 t_col, s_col, n_col = st.columns([1.5, 2.5, 4])
    #                 t_col.write(f"⏰ {row['開始時間']} ~ {row['結束時間']}")
    #                 s_col.markdown(f"**{row['活動']}** [📍]({row['地圖連結']})")
    #                 n_col.caption(row['備註'])

    #                 # if i == 0 and len(basic_data) > 4 and basic_data[4]:
    #                 #     t_col, s_col, n_col = st.columns([1, 2, 4])
    #                 #     t_col.write("✈️ 飛行")
    #                 #     # 這裡顯示已經被 AI 格式化過的文字
    #                 #     s_col.info(basic_data[4]) 
    #                 #     n_col.caption("記得提前 2-3 小時抵達機場報到")
    #                 #     st.divider() # 加一條線區隔航班與後續地面行程

    #                 # --- 2. 計算交通時間 (如果還有下一個行程) ---
    #                 if i < len(items_list) - 1:
    #                     next_row = items_list[i+1]
    #                     travel_info = get_travel_time(row['活動'], next_row['活動'], country_name)
    #                     if travel_info:
    #                         st.caption(f"  └ 🚶 {travel_info}")
    #         else:
    #             st.caption("今天暫無行程")
    
    
    @st.dialog("➕ 新增行程項目")
    def add_item_dialog():
        with st.form("dialog_form", clear_on_submit=True):
            d = st.selectbox("日期", options=date_range)
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                t_start = st.text_input("開始時間 (HH:MM)", placeholder="09:00")
            with col_t2:
                t_end = st.text_input("結束時間 (HH:MM)", placeholder="10:30")
            s = st.text_input("景點/餐廳名稱")
            n = st.text_area("備註")
            map_url = st.text_input("地圖連結 ", placeholder="https://maps.google.com/...") 
            if not map_url:
                import urllib.parse
                map_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(f'{country_name} {s}')}"
            
            if st.form_submit_button("確認新增"):
                if d and t_start and s:
                    current_sheet.append_row([d, t_start, t_end, s, map_url, n])
                    st.success("已加入行程！")
                    st.rerun()
                else:
                    st.error("請至少填寫開始時間與景點名稱")
    
    if st.button("➕ 添加新景點", use_container_width=True):
      add_item_dialog()


with st.sidebar:
    st.divider()
    
    def get_travel_meta_json(raw_text, travel_start):
        
        prompt = f"""
        請分析以下旅遊資訊（包含航班或酒店）並轉換為結構化 JSON。
        參考開始日期：{travel_start}
        輸入內容：{raw_text}
        
        請嚴格遵守以下 JSON 格式：
        {{
            "航班號": "...", "出發機場": "...", "出發時間": "HH:MM", 
            "抵達機場": "...", "抵達時間": "HH:MM",
            "酒店名稱": "...", "酒店地址": "...", "入住日期": "YYYY-MM-DD", "退房日期": "YYYY-MM-DD"
        }}
        如果資訊中沒有提到某項，請填入空字串 ""。請直接輸出純 JSON 字串。
        """
        try:
            response = model.generate_content(prompt)
            clean_text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_text)
        except Exception as e:
            st.error(f"AI 解析出錯：{e}")
            return None
    
        





