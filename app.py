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
        st.markdown("""
            <div style='text-align: center; padding: 2rem 0;'>
                <h2 style='color: #1e293b; font-family: sans-serif;'>太田家 資産管理</h2>
                <p style='color: #64748b;'>Security Portal</p>
            </div>
        """, unsafe_allow_html=True)
        st.text_input("パスワードを入力してください", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("😕 パスワードが違います")
        return False
    return True

if check_password():
    # --- 🏛️ モバイル最適化・モダンUIカスタムCSS ---
    st.markdown("""
    <style>
        /* 全体背景とフォント */
        .stApp { background-color: #f8fafc; }
        
        /* 見切れ防止：フレキシブル・メインタイトル */
        .main-title {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            color: #ffffff;
            padding: 1.5rem 1rem;
            border-radius: 12px;
            font-size: 1.4rem !important;
            font-weight: 700;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            line-height: 1.4;
            text-align: center;
        }

        /* サブヘッダーのスマホ最適化 */
        .small-subheader {
            font-size: 1.1rem !important;
            font-weight: 700;
            color: #0f172a;
            margin: 1.5rem 0 0.8rem 0.2rem;
            border-left: 4px solid #2563eb;
            padding-left: 10px;
        }

        /* 指標カード（メトリクス）のデザイン改善 */
        div[data-testid="metric-container"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 1rem !important;
            box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
            transition: transform 0.2s;
        }
        div[data-testid="stMetricLabel"] > div {
            font-size: 0.85rem !important;
            color: #64748b !important;
            font-weight: 600;
            margin-bottom: 0.3rem;
        }
        div[data-testid="stMetricValue"] > div {
            font-size: 1.5rem !important;
            font-weight: 800 !important;
            color: #1e293b !important; /* 紺からチャコールグレーへ（視認性UP） */
        }

        /* 予測バー（スマホで目に飛び込む青系グラデ） */
        .projection-bar {
            background-color: #eff6ff;
            padding: 1.2rem;
            border-radius: 16px;
            margin: 1.5rem 0;
            border: 1px solid #bfdbfe;
        }
        
        /* タブのスタイル調整 */
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] {
            background-color: #f1f5f9;
            border-radius: 8px 8px 0 0;
            padding: 10px 20px;
            color: #475569;
        }
        .stTabs [aria-selected="true"] {
            background-color: #2563eb !important;
            color: white !important;
        }

        /* NISAバー */
        .nisa-bar {
            background-color: #ffffff;
            padding: 1.2rem;
            border-radius: 16px;
            margin-top: 2rem;
            border: 1px solid #e2e8f0;
            border-top: 4px solid #2563eb;
        }

        /* スマホでのスクロール余白 */
        .block-container { padding: 1.5rem 1rem !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="main-title">太田家 資産管理システム</p>', unsafe_allow_html=True)

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

    tab_p1, tab_data = st.tabs(["現状維持シミュレーション", "📂 データ詳細確認"])

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

            st.markdown('<p class="small-subheader">現在資産状況</p>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            c1.metric("総資産額", f"{val_total/10000:,.0f} 万円")
            c2.metric("高配当投信", f"{val_k/10000:,.0f} 万円")
            c3, c4 = st.columns(2)
            c3.metric("NISA口座", f"{val_nisa_current/10000:,.0f} 万円")
            c4.metric("年金 (DC/iDeCo)", f"{val_nenkin_current/10000:,.0f} 万円")

            st.markdown('<p class="small-subheader">将来予測シミュレーション</p>', unsafe_allow_html=True)
            st.markdown("<div class='projection-bar'>", unsafe_allow_html=True)
            m1, m2 = st.columns(2)
            m1.metric(f"{years}年後 予測総資産", f"{history[-1]/10000:,.0f} 万円")
            m2.metric("累計拠出元本", f"{principal/10000:,.0f} 万円")
            m3, m4 = st.columns(2)
            m3.metric("年間配当受取", f"{(sim_k*0.035)/10000:,.0f} 万円")
            m4.metric("月間配当受取", f"{(sim_k*0.035/12):,.0f} 円")
            st.markdown("</div>", unsafe_allow_html=True)

            # グラフ表示
            st.markdown('<p class="small-subheader">ポートフォリオ（拠出金）</p>', unsafe_allow_html=True)
            data_b = {
                'カテゴリ': ["高配当", "オルカン", "日本株", "その他", "高配当", "オルカン", "日本株", "その他"],
                '金額(万円)': [val_k/10000, val_o/10000, val_j/10000, val_others/10000, p_k/10000, p_o/10000, p_j/10000, p_others/10000],
                'タイミング': ["現在", "現在", "現在", "現在", f"{years}年後", f"{years}年後", f"{years}年後", f"{years}年後"]
            }
            df_b = pd.DataFrame(data_b)
            df_b['比率'] = df_b.apply(lambda row: (row['金額(万円)'] * 10000) / val_total * 100 if row['タイミング'] == "現在" else (row['金額(万円)'] * 10000) / principal * 100, axis=1)
            df_b['text'] = df_b.apply(lambda row: f"{row['比率']:.1f}%<br>({row['金額(万円)']:.0f}万)", axis=1)
            fig_b = px.bar(df_b, x='タイミング', y='金額(万円)', color='カテゴリ', barmode='stack', text='text', color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_b.update_layout(height=400, margin=dict(t=10, b=10, l=10, r=10), plot_bgcolor='rgba(0,0,0,0)', font=dict(size=11))
            st.plotly_chart(fig_b, use_container_width=True)

            st.markdown('<p class="small-subheader">資産推移グラフ</p>', unsafe_allow_html=True)
            fig_g = go.Figure(go.Scatter(x=years_list, y=[h/10000 for h in history], mode='lines+markers', line=dict(color='#2563eb', width=3), fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.1)'))
            fig_g.update_layout(height=400, margin=dict(t=10, b=10, l=10, r=10), plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(gridcolor='#e2e8f0'), yaxis=dict(gridcolor='#e2e8f0'))
            st.plotly_chart(fig_g, use_container_width=True)

            # NISA残枠
            nisa_rem_total = max(0, 36000000 - nisa_used_total)
            nisa_rem_growth = min(nisa_rem_total, max(0, 24000000 - nisa_used_growth))
            st.markdown("<div class='nisa-bar'>", unsafe_allow_html=True)
            st.markdown(f"**{years}年後のNISA残枠（世帯合計）**")
            n1, n2 = st.columns(2)
            n1.metric("総枠残り", f"{nisa_rem_total/10000:,.0f} 万円")
            n2.metric("うち成長枠", f"{nisa_rem_growth/10000:,.0f} 万円")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_data:
        st.subheader("📂 登録資産データ一覧")
        if not df.empty:
            df_display = df[['owner', 'account', 'item_name', 'cat', 'value']].copy()
            df_display.columns = ['所有者', '口座', '商品名', 'カテゴリ', '評価額']
            df_display['評価額'] = df_display['評価額'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(df_display, use_container_width=True)
