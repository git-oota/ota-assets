import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# --- ページ設定 ---
st.set_page_config(page_title="資産管理 | 太田家", layout="wide", initial_sidebar_state="expanded")

# --- 🔐 セキュリティ：簡易パスワード認証 ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "yayoi1005":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # スマホのダークモードによる文字の白化を絶対に許さない最優先CSS
        st.markdown("""
        <style>
            * {
                color: #000000 !important; 
                -webkit-text-fill-color: #000000 !important;
            }
            h2, p, label, input {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
            }
            input[type="password"] {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
                background-color: #ffffff !important;
                border: 2px solid #000000 !important;
            }
        </style>
        <div style='text-align: center; padding: 2rem 0; font-family: system-ui, sans-serif;'>
            <h2 style='font-weight: 800; font-size: 1.8rem;'>太田家 資産管理</h2>
            <p style='font-weight: 600; font-size: 0.9rem; color: #000000 !important;'>Private Wealth Portal</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.text_input("パスワードを入力してください", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("😕 パスワードが違います")
        return False
    return True

if check_password():
    # --- 🏆 PCとスマホを完全に切り分ける究極のレスポンシブCSS ---
    st.markdown("""
    <style>
        /* ベース環境 */
        .stApp { background-color: #ffffff !important; }
        .block-container { padding: 1.5rem 1.5rem !important; max-width: 96% !important; }
        
        /* タイトルエリア */
        .main-title {
            background: #111111 !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            padding: 1.2rem;
            border-radius: 12px;
            font-size: 1.4rem !important;
            font-weight: 800;
            margin-bottom: 1.5rem;
            text-align: center;
        }

        /* サブヘッダーフォント（1回り小さく） */
        .small-subheader {
            font-size: 1.1rem !important;
            font-weight: 800;
            color: #111111 !important;
            margin: 1.5rem 0 0.8rem 0.2rem;
            padding-left: 10px;
            border-left: 5px solid #111111;
        }

        /* 💻 【PCサイトの標準設定（元の広々とした1行横並びを完全復活）】 */
        div[data-testid="stMetric"] {
            background: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 12px !important;
            padding: 0.8rem 1.2rem !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
        }
        div[data-testid="stMetricLabel"] > div {
            font-size: 0.85rem !important;
            color: #475569 !important;
            font-weight: 700 !important;
        }
        div[data-testid="stMetricValue"] > div {
            font-size: 1.6rem !important;
            font-weight: 800 !important;
            color: #0f172a !important;
        }
        .projection-bar {
            background-color: #f8fafc !important;
            padding: 1.2rem;
            border-radius: 14px;
            margin: 1.5rem 0;
            border: 1px solid #e2e8f0;
        }
        .nisa-bar {
            background-color: #ffffff !important;
            padding: 1.2rem;
            border-radius: 14px;
            margin-top: 2rem;
            border: 1px solid #cbd5e1 !important;
            border-top: 5px solid #10b981 !important;
        }

        /* 📱 【スマホ画面(横幅640px以下)限定】3列化 ＆ 文字黒固定ルール */
        @media (max-width: 640px) {
            .block-container { padding: 1rem 0.5rem !important; }
            
            /* スマホ時のみ文字・数値を絶対に真っ黒にする強制設定 */
            div[data-testid="stMetricLabel"] > div, 
            div[data-testid="stMetricValue"] > div,
            .small-subheader, p, span, label {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
            }

            /* 横並びの列（columns）を強制的に3列1行に詰め込む */
            div[data-testid="stHorizontalBlock"] {
                display: flex !important;
                flex-direction: row !important;
                flex-wrap: nowrap !important;
                gap: 4px !important;
            }
            div[data-testid="stHorizontalBlock"] > div {
                flex: 1 1 33.33% !important;
                min-width: 0 !important;
            }
            
            /* スマホ用：黒枠のコンパクトカード */
            div[data-testid="stMetric"] {
                padding: 0.4rem 0.2rem !important;
                border-radius: 8px !important;
                border: 1.5px solid #000000 !important;
                box-shadow: none !important;
            }
            /* スマホ用項目名（ラベル） */
            div[data-testid="stMetricLabel"] > div {
                font-size: 0.65rem !important;
                font-weight: 900 !important;
                letter-spacing: -0.04em !important;
                line-height: 1.1 !important;
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
            }
            /* スマホ用数値 */
            div[data-testid="stMetricValue"] > div {
                font-size: 1.1rem !important;
                font-weight: 900 !important;
                letter-spacing: -0.05em !important;
            }
            .projection-bar {
                background-color: #f1f5f9 !important;
                border: 2px solid #cbd5e1 !important;
                padding: 0.8rem;
            }
            .nisa-bar {
                border: 2px solid #000000 !important;
                padding: 0.8rem;
            }
        }

        /* タブのスタイル */
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            background-color: #e2e8f0 !important;
            border-radius: 16px;
            padding: 6px 16px;
            font-size: 0.85rem !important;
            font-weight: 700;
        }
        .stTabs [aria-selected="true"] {
            background: #111111 !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="main-title">太田家 資産管理ダッシュボード</p>', unsafe_allow_html=True)

    # --- 🚀 データエンジン ---
    DATA_FILE = 'assets_db.json'
    df = pd.read_json(DATA_FILE) if os.path.exists(DATA_FILE) else pd.DataFrame()

    def categorize(name):
        n = str(name)
        if "現金" in n: return "現金"
        if any(k in n for k in ["高配当", "分配"]): return "高配当"
        if any(k in n for k in ["全世界", "オール・カントリー"]): return "オルカン"
        if "日経平均" in n: return "日本株"
        if any(k in n for k in ["金", "NTT", "インド"]): return "その他"
        return "その他"

    if not df.empty:
        required_cols = ['owner', 'account', 'item_name', 'value']
        if all(col in df.columns for col in required_cols):
            if 'updated_at' in df.columns:
                df = df.sort_values('updated_at')
            df = df.drop_duplicates(subset=['owner', 'account', 'item_name'], keep='last')
            df['cat'] = df['item_name'].apply(categorize)
            df['value'] = pd.to_numeric(df['value'], errors='coerce').fillna(0)

    # --- サイドバー設定 ---
    st.sidebar.header("📊 分析条件設定")
    years = st.sidebar.slider("運用期間 (年)", min_value=1, max_value=30, value=5)
    growth_rate = st.sidebar.slider("期待利回り (%)", min_value=0.0, max_value=15.0, value=5.0) / 100
    st.sidebar.markdown("**配当利回り:** 3.5% (固定)")

    start_year, start_month = 2026, 5
    current_year, current_month = datetime.now().year, datetime.now().month
    elapsed_months = (current_year - start_year) * 12 + (current_month - start_month)
    remaining_months = max(0, 64 - max(0, elapsed_months))
    st.sidebar.markdown(f"**残り積立月数:** {remaining_months} ヶ月")

    tab_p1, tab_data = st.tabs(["現状維持シミュレーション", "📂 データ確認"])

    with tab_p1:
        if not df.empty:
            val_total = df['value'].sum()
            val_k = df[df['cat'] == "高配当"]['value'].sum()
            val_o = df[df['cat'] == "オルカン"]['value'].sum()
            val_j = df[df['cat'] == "日本株"]['value'].sum()
            val_others = df[df['cat'] == "その他"]['value'].sum() + df[df['cat'] == "現金"]['value'].sum()

            val_nisa_current = df[df['account'] == 'NISA']['value'].sum()
            val_nenkin_current = df[df['account'].isin(['DC', 'iDeCo'])]['value'].sum()

            sim_k, sim_o, sim_j, sim_others = val_k, val_o, val_j, val_others
            p_k, p_o, p_j, p_others = val_k, val_o, val_j, val_others
            principal = val_total
            nisa_used_total, nisa_used_growth = val_nisa_current, df[(df['account'] == 'NISA') & (df['cat'] == '高配当')]['value'].sum()
            history, years_list = [val_total], [current_year]

            monthly_k, monthly_o, monthly_j = 200000, 25000, 25000

            for i in range(1, years + 1):
                for m in range(12):
                    sim_month_total = (current_year * 12 + current_month - 1) + (i - 1) * 12 + m
                    sim_y, sim_m = sim_month_total // 12, (sim_month_total % 12) + 1
                    months_since_start = (sim_y - start_year) * 12 + (sim_m - start_month)
                    
                    if 0 <= months_since_start < 64:
                        sim_k += monthly_k; sim_o += monthly_o; sim_j += monthly_j
                        p_k += monthly_k; p_o += monthly_o; p_j += monthly_j
                        principal += (monthly_k + monthly_o + monthly_j)
                        nisa_used_growth += monthly_k; nisa_used_total += monthly_k

                    if sim_y == 2026 and sim_m == 5 and i == 1 and m == 0:
                        sim_j += 2400000; sim_others += 1200000
                        p_j += 2400000; p_others += 1200000
                        principal += 3600000; nisa_used_total += 2400000
                    
                    if sim_y == 2027 and sim_m == 1:
                        sim_k += 2400000; p_k += 2400000; principal += 2400000
                        nisa_used_growth += 2400000; nisa_used_total += 2400000

                    sim_k *= (1 + growth_rate)**(1/12); sim_o *= (1 + growth_rate)**(1/12)
                    sim_j *= (1 + growth_rate)**(1/12); sim_others *= (1 + growth_rate)**(1/12)

                history.append(sim_k + sim_o + sim_j + sim_others)
                years_list.append(current_year + i)

            # 📊 現在資産状況（PCでは広々1行並び、スマホでは自動で3列2段に可変）
            st.markdown('<p class="small-subheader">現在資産状況</p>', unsafe_allow_html=True)
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric("総資産額", f"{val_total/10000:,.0f}万")
            c2.metric("高配当投信", f"{val_k/10000:,.0f}万")
            c3.metric("NISA口座", f"{val_nisa_current/10000:,.0f}万")
            c4.metric("年金(DC)", f"{val_nenkin_current/10000:,.0f}万")
            c5.metric("日経平均", f"{val_j/10000:,.0f}万")
            c6.metric("現金他", f"{val_others/10000:,.0f}万")

            # 🔮 将来予測（PCでは広々1行並び、スマホでは自動で3列2段に可変）
            st.markdown('<p class="small-subheader">将来予測シミュレーション</p>', unsafe_allow_html=True)
            st.markdown("<div class='projection-bar'>", unsafe_allow_html=True)
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric(f"{years}年後予測", f"{history[-1]/10000:,.0f}万")
            m2.metric("累計拠出元本", f"{principal/10000:,.0f}万")
            m3.metric("高配当予測", f"{sim_k/10000:,.0f}万")
            m4.metric("年間配当", f"{(sim_k*0.035)/10000:,.0f}万")
            m5.metric("月間配当受取", f"{(sim_k*0.035/12):,.0f}円")
            m6.metric("残り積立", f"{remaining_months}ヶ月")
            st.markdown("</div>", unsafe_allow_html=True)

            # グラフ表示領域を左右に均等配置（大画面のPCサイトを引き続き維持）
            g_l, g_r = st.columns([1, 1])
            with g_l:
                st.markdown("**ポートフォリオ（拠出金）**")
                data_b = {
                    'カテゴリ': ["高配当", "オルカン", "日本株", "その他", "高配当", "オルカン", "日本株", "その他"],
                    '金額(万円)': [val_k/10000, val_o/10000, val_j/10000, val_others/10000, p_k/10000, p_o/10000, p_j/10000, p_others/10000],
                    'タイミング': ["現在", "現在", "現在", "現在", f"{years}年後", f"{years}年後", f"{years}年後", f"{years}年後"]
                }
                df_b = pd.DataFrame(data_b)
                df_b['比率'] = df_b.apply(lambda row: (row['金額(万円)'] * 10000) / val_total * 100 if row['タイミング'] == "現在" else (row['金額(万円)'] * 10000) / principal * 100, axis=1)
                df_b['text'] = df_b.apply(lambda row: f"{row['比率']:.1f}%<br>({row['金額(万円)']:.0f}万)", axis=1)
                
                fig_b = px.bar(df_b, x='タイミング', y='金額(万円)', color='カテゴリ', barmode='stack', text='text', color_discrete_sequence=px.colors.qualitative.Safe)
                fig_b.update_layout(height=420, margin=dict(t=10, b=10, l=5, r=5), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(size=11), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_b, use_container_width=True)

            with g_r:
                st.markdown(f"**資産推移グラフ（{years}年間連動）**")
                fig_g = go.Figure(go.Scatter(x=years_list, y=[h/10000 for h in history], mode='lines+markers', line=dict(color='#3b82f6', width=3), fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.05)'))
                fig_g.update_layout(height=420, margin=dict(t=10, b=10, l=5, r=5), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict(gridcolor='#e2e8f0'), yaxis=dict(gridcolor='#e2e8f0'))
                st.plotly_chart(fig_g, use_container_width=True)

            # NISA残枠
            nisa_rem_total = max(0, 36000000 - nisa_used_total)
            nisa_rem_growth = min(nisa_rem_total, max(0, 24000000 - nisa_used_growth))
            st.markdown("<div class='nisa-bar'>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-weight:800; color:#000000; margin-bottom:0.5rem;'>🎯 {years}年後のNISA残枠（世帯合計）</p>", unsafe_allow_html=True)
            n1, n2, n3 = st.columns(3)
            n1.metric("総枠残り", f"{nisa_rem_total/10000:,.0f}万")
            n2.metric("うち成長枠", f"{nisa_rem_growth/10000:,.0f}万")
            n3.metric("積立終了", "2031年8月")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_data:
        st.subheader("📂 登録資産データ一覧")
        if not df.empty:
            df_display = df[['owner', 'account', 'item_name', 'cat', 'value']].copy()
            df_display.columns = ['所有者', '口座', '商品名', 'カテゴリ', '評価額']
            df_display['評価額'] = df_display['評価額'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(df_display, use_container_width=True)
