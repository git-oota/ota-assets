import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# --- ページ設定 ---
st.set_page_config(page_title="資産管理 | 太田家", layout="wide", initial_sidebar_state="expanded")

# --- 🏛️ 金融機関・コンサルティング風カスタムCSS ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; max-width: 96% !important; }
    .main-title { background-color: #12234D; color: #FFFFFF; padding: 10px 20px; border-radius: 4px; font-size: 1.2rem !important; font-weight: 700; margin-bottom: 15px; border-left: 8px solid #2E5BFF; }
    .small-subheader { font-size: 1.1rem !important; font-weight: 600; color: #12234D; margin-top: 10px; margin-bottom: 10px; }
    div[data-testid="metric-container"] { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 4px; padding: 8px 12px !important; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    div[data-testid="stMetricLabel"] > div { font-size: 0.75rem !important; color: #64748B !important; font-weight: 600; }
    div[data-testid="stMetricValue"] > div { font-size: 1.25rem !important; font-weight: 700 !important; color: #12234D !important; }
    .projection-bar { background-color: #F8FAFC; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-top: 2px solid #1E3A8A; }
    .nisa-bar { background-color: #FFFFFF; padding: 15px; border-radius: 8px; margin-top: 20px; border: 1px solid #E2E8F0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">💼 資産管理</p>', unsafe_allow_html=True)

# --- 🚀 データエンジン ---
DATA_FILE = 'assets_db.json'

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            return pd.read_json(DATA_FILE)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

df = load_data()
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
    else:
        st.error("JSONデータに必要な項目が含まれていません。")
        df = pd.DataFrame()

# --- 📊 画面左側：サイドバー設定 ---
st.sidebar.header("📊 分析条件設定")
years = st.sidebar.slider("運用期間 (年)", min_value=1, max_value=30, value=5)
growth_rate = st.sidebar.slider("期待利回り (%)", min_value=0.0, max_value=15.0, value=5.0) / 100
st.sidebar.markdown("**配当利回り:** 3.5% (固定)")

# 📅 残り積立月数の動的計算 (2026年5月をスタートとして自動減算)
start_year = 2026
start_month = 5
current_year = datetime.now().year
current_month = datetime.now().month
elapsed_months = (current_year - start_year) * 12 + (current_month - start_month)
remaining_months = max(0, 64 - max(0, elapsed_months))
st.sidebar.markdown(f"**残り積立月数:** {remaining_months} ヶ月 (自動減算中)")

# --- ページ構成：2つのタブ ---
tab_p1, tab_data = st.tabs(["現状維持", "📂 データ確認"])

# --- 現状維持タブ ---
with tab_p1:
    if not df.empty:
        val_total = df['value'].sum()
        val_cash = df[df['cat'] == "現金"]['value'].sum()
        val_k = df[df['cat'] == "高配当"]['value'].sum()
        val_o = df[df['cat'] == "オルカン"]['value'].sum()
        val_j = df[df['cat'] == "日本株"]['value'].sum()
        val_others = df[df['cat'] == "その他"]['value'].sum()

        val_nisa_current = df[df['account'] == 'NISA']['value'].sum()
        val_nenkin_current = df[df['account'].isin(['DC', 'iDeCo'])]['value'].sum()
        val_nisa_growth_current = df[(df['account'] == 'NISA') & (df['cat'] == '高配当')]['value'].sum()

        # 口座属性別のシミュレーション用初期値
        sim_nisa = val_nisa_current
        sim_nenkin = val_nenkin_current
        p_nisa = val_nisa_current
        p_nenkin = val_nenkin_current

        # シミュレーション用変数 (カテゴリ別運用利回り計算用)
        sim_cash = val_cash
        sim_k, sim_o, sim_j, sim_others = val_k, val_o, val_j, val_others

        # 拠出金（元本）のみを純粋に追跡する変数
        p_cash = val_cash
        p_k, p_o, p_j, p_others = val_k, val_o, val_j, val_others
        principal = val_total

        nisa_used_total = val_nisa_current
        nisa_used_growth = val_nisa_growth_current
        history = [val_total]
        years_list = [current_year]

        # 毎月の積立設定金額
        monthly_k = 200000
        monthly_o = 25000
        monthly_j = 25000

        # シミュレーションループ
        for i in range(1, years + 1):
            for m in range(12):
                # シミュレーション上の具体的な年月を算出
                sim_month_total = (current_year * 12 + current_month - 1) + (i - 1) * 12 + m
                sim_y = sim_month_total // 12
                sim_m = (sim_month_total % 12) + 1

                # 計画開始（2026年5月）からの通算月数を計算
                months_since_start = (sim_y - start_year) * 12 + (sim_m - start_month)

                # 📌 計画開始から64ヶ月未満の間だけ積立を実行
                if 0 <= months_since_start < 64:
                    sim_k += monthly_k
                    sim_o += monthly_o
                    sim_j += monthly_j

                    p_k += monthly_k
                    p_o += monthly_o
                    p_j += monthly_j
                    principal += (monthly_k + monthly_o + monthly_j)

                    # 積立はすべてNISA口座を想定
                    sim_nisa += (monthly_k + monthly_o + monthly_j)
                    p_nisa += (monthly_k + monthly_o + monthly_j)

                    nisa_used_growth += monthly_k
                    nisa_used_total += monthly_k

                # 利回りの適用 (月次複利) ※0%の場合は計算しない。現金(sim_cash)は利回り計算から除外
                if growth_rate > 0:
                    factor = (1 + growth_rate)**(1/12)
                    sim_k *= factor
                    sim_o *= factor
                    sim_j *= factor
                    sim_others *= factor

                    sim_nisa *= factor
                    sim_nenkin *= factor

            # 現金を含めた総資産額を履歴に追加
            history.append(sim_cash + sim_k + sim_o + sim_j + sim_others)
            years_list.append(current_year + i)

        # NISA残枠計算
        nisa_rem_total = max(0, 36000000 - nisa_used_total)
        nisa_rem_growth_raw = max(0, 24000000 - nisa_used_growth)
        nisa_rem_growth = min(nisa_rem_total, nisa_rem_growth_raw)

        # 各口座の値上がり率算出（分母が0の場合は0.0%）
        roi_nisa = ((sim_nisa - p_nisa) / p_nisa * 100) if p_nisa > 0 else 0.0
        roi_nenkin = ((sim_nenkin - p_nenkin) / p_nenkin * 100) if p_nenkin > 0 else 0.0

        # サブヘッダー
        st.markdown('<p class="small-subheader">現在資産 ＆ 将来予測</p>', unsafe_allow_html=True)

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("現在の総資産額", f"{val_total/10000:,.0f} 万円")
        c2.metric("現金 (現在)", f"{val_cash/10000:,.0f} 万円")
        c3.metric("NISA口座 (現在)", f"{val_nisa_current/10000:,.0f} 万円")
        c4.metric("DC / iDeCo (現在)", f"{val_nenkin_current/10000:,.0f} 万円")
        c5.metric("高配当投信 (現在)", f"{val_k/10000:,.0f} 万円")

        st.markdown("<div class='projection-bar'>", unsafe_allow_html=True)
        m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
        m1.metric(f"{years}年後 予測総資産額", f"{history[-1]/10000:,.0f} 万円")
        m2.metric("累計拠出元本", f"{principal/10000:,.0f} 万円")
        m3.metric("NISA 予測額", f"{sim_nisa/10000:,.0f} 万円", f"+{roi_nisa:.1f}%" if roi_nisa > 0 else f"{roi_nisa:.1f}%")
        m4.metric("DC/iDeCo 予測", f"{sim_nenkin/10000:,.0f} 万円", f"+{roi_nenkin:.1f}%" if roi_nenkin > 0 else f"{roi_nenkin:.1f}%")
        m5.metric("高配当 予測評価額", f"{sim_k/10000:,.0f} 万円")
        m6.metric("年間配当 (3.5%想定)", f"{(sim_k*0.035)/10000:,.0f} 万円")
        m7.metric("月間配当受取額", f"{(sim_k*0.035/12):,.0f} 円")
        st.markdown("</div>", unsafe_allow_html=True)

        g_l, g_r = st.columns([1, 1])

        with g_l:
            st.markdown("**ポートフォリオ（拠出金）**")
            data_b = {
                'カテゴリ': ["現金", "高配当", "オルカン", "日本株", "その他", "現金", "高配当", "オルカン", "日本株", "その他"],
                '金額(万円)': [val_cash/10000, val_k/10000, val_o/10000, val_j/10000, val_others/10000, p_cash/10000, p_k/10000, p_o/10000, p_j/10000, p_others/10000],
                'タイミング': ["現在", "現在", "現在", "現在", "現在", f"{years}年後", f"{years}年後", f"{years}年後", f"{years}年後", f"{years}年後"]
            }
            df_b = pd.DataFrame(data_b)
            df_b['比率'] = df_b.apply(lambda row: (row['金額(万円)'] * 10000) / val_total * 100 if row['タイミング'] == "現在" else (row['金額(万円)'] * 10000) / principal * 100, axis=1)
            df_b['表示用テキスト'] = df_b.apply(lambda row: f"{row['比率']:.1f}%<br>({row['金額(万円)']:.0f}万)", axis=1)

            fig_b = px.bar(df_b, x='タイミング', y='金額(万円)', color='カテゴリ', barmode='stack', text='表示用テキスト', color_discrete_sequence=px.colors.qualitative.Vivid)
            fig_b.update_traces(textposition='inside', insidetextanchor='middle')
            fig_b.update_layout(height=450, margin=dict(t=10, b=30, l=10, r=10), plot_bgcolor='white', xaxis=dict(showgrid=False, title_text='', tickfont=dict(size=14)), yaxis=dict(showgrid=True, gridcolor='#F1F5F9', title_text='純拠出金額 (万円)'), font=dict(size=12))
            st.plotly_chart(fig_b, use_container_width=True)

        with g_r:
            st.markdown(f"**資産推移グラフ（{years}年間連動）**")
            fig_g = go.Figure(go.Scatter(x=years_list, y=[h/10000 for h in history], mode='lines', line=dict(color='#1E3A8A', width=3), fill='tozeroy'))
            fig_g.update_layout(height=450, margin=dict(t=10, b=30, l=10, r=10), plot_bgcolor='white', xaxis=dict(showgrid=True, gridcolor='#F1F5F9', tickformat="yyyy"), yaxis=dict(showgrid=True, gridcolor='#F1F5F9', title_text='総資産予測額 (万円)'))
            st.plotly_chart(fig_g, use_container_width=True)

        st.markdown("<div class='nisa-bar'>", unsafe_allow_html=True)
        n1, n2, n3 = st.columns([1, 1, 3])
        n1.metric(f"{years}年後 NISA残枠 (世帯合計)", f"{nisa_rem_total/10000:,.0f} 万円")
        n2.metric("うち 成長投資枠 残り", f"{nisa_rem_growth/10000:,.0f} 万円")
        n3.markdown("<div style='font-size: 0.75rem; color: #64748B; margin-top: 18px;'>※ スライダーで指定した期間の終了時点における、世帯のNISA非課税投資残枠のシミュレーションです。</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("有効なデータが見つかりません。データ確認タブから状況をご確認ください。")

# --- データ確認タブ ---
with tab_data:
    st.subheader("📥 取り込みデータ一覧")
    if not df.empty:
        df_display = df[['owner', 'account', 'item_name', 'cat', 'value']].copy()
        df_display.columns = ['所有者', '口座', 'ファンド名 / 商品名', '自動判定カテゴリ', '評価額 (円)']
        df_display['評価額 (円)'] = df_display['評価額 (円)'].apply(lambda x: f"{x:,.0f}")
        st.dataframe(df_display, use_container_width=True)
    else:
        st.warning("データがありません。")
