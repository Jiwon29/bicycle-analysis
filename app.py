import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="따릉이 타겟팅 대시보드", layout="wide", page_icon="🚴")

st.title("🚴 따릉이 팝업광고 타겟팅 최적화 분석")
st.markdown("정기권과 일일권 이용 패턴을 분석하여 **최적의 광고 타겟**을 선정합니다.")

DB_PATH = "자전거분석_slim.db"

@st.cache_data
def load(query):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ── KPI 카드 ──────────────────────────────────────────────
df_usage = load("SELECT * FROM 이용건수집계")
total = df_usage['이용건수합계'].sum()
jeong_cnt = df_usage.loc[df_usage['권종그룹']=='정기권','이용건수합계'].values[0]
ilil_cnt  = df_usage.loc[df_usage['권종그룹']=='일일권','이용건수합계'].values[0]

k1,k2,k3,k4 = st.columns(4)
k1.metric("총 이용건수", f"{total/10000:.0f}만 건")
k2.metric("정기권 이용건수", f"{jeong_cnt/10000:.0f}만 건", f"{jeong_cnt/total*100:.1f}%")
k3.metric("일일권 이용건수", f"{ilil_cnt/10000:.0f}만 건", f"{ilil_cnt/total*100:.1f}%")
k4.metric("분석 대여소 수", "2,795개소")
st.divider()


# ── 섹션 1: 이용 지역 지도 ──────────────────────────────
st.header("1. 이용권별 주요 이용 지역 (TOP 100)")

df_map = load("""
    SELECT 보관소명 AS 대여소명, 자치구, 위도 AS lat, 경도 AS lon,
           권종그룹, 이용건수합계
    FROM 지역집계
    WHERE 위도 IS NOT NULL AND 경도 IS NOT NULL
""")

tab_j, tab_i = st.tabs(["📍 정기권 TOP 100", "📍 일일권 TOP 100"])

with tab_j:
    df_j = df_map[df_map['권종그룹']=='정기권'].nlargest(100,'이용건수합계')
    fig_j = px.scatter_mapbox(
        df_j, lat='lat', lon='lon', size='이용건수합계',
        hover_name='대여소명', hover_data={'자치구':True,'이용건수합계':True,'lat':False,'lon':False},
        color='이용건수합계', color_continuous_scale='Blues',
        size_max=18, zoom=10.5, height=480,
        mapbox_style='carto-positron',
        title='정기권 이용 집중 지역 — 마곡·영등포·강남 역세권'
    )
    fig_j.update_layout(margin=dict(l=0,r=0,t=40,b=0))
    st.plotly_chart(fig_j, use_container_width=True)
    st.info("**인사이트:** 마곡나루·영등포·강남 등 역세권 및 산업단지 중심. 출퇴근 교통수단으로 활용하는 **정기 통근자** 타겟 최적.")
    with st.expander("사용 테이블"):
        st.code("지역집계 (대여구분코드='정기권' 기준 집계)")

with tab_i:
    df_i = df_map[df_map['권종그룹']=='일일권'].nlargest(100,'이용건수합계')
    fig_i = px.scatter_mapbox(
        df_i, lat='lat', lon='lon', size='이용건수합계',
        hover_name='대여소명', hover_data={'자치구':True,'이용건수합계':True,'lat':False,'lon':False},
        color='이용건수합계', color_continuous_scale='Greens',
        size_max=18, zoom=10.5, height=480,
        mapbox_style='carto-positron',
        title='일일권 이용 집중 지역 — 한강공원·관광지 중심'
    )
    fig_i.update_layout(margin=dict(l=0,r=0,t=40,b=0))
    st.plotly_chart(fig_i, use_container_width=True)
    st.info("**인사이트:** 망원·뚝섬·여의도 한강선착장·한강공원 집중. 주말 나들이·레저 목적의 **일회성 이용자** 타겟 최적.")
    with st.expander("사용 테이블"):
        st.code("지역집계 (대여구분코드 LIKE '%일일권%' 기준 집계)")

st.divider()


# ── 섹션 2: 성별 분포 ────────────────────────────────────
st.header("2. 권종별 이용 성별 분포")

df_gender = load("SELECT * FROM 성별집계 WHERE 권종그룹 != '기타' AND 성별 IN ('M','F')")
df_gender['성별'] = df_gender['성별'].map({'M':'남성','F':'여성'})

col1, col2 = st.columns(2)
for col, grp, color_seq in [(col1,'정기권',['#0C447C','#85B7EB']),(col2,'일일권',['#085041','#5DCAA5'])]:
    with col:
        df_g = df_gender[df_gender['권종그룹']==grp]
        fig = px.pie(df_g, values='이용건수합계', names='성별',
                     title=f"{grp} 성별 구성",
                     color_discrete_sequence=color_seq,
                     hole=0.42)
        fig.update_traces(textposition='inside', textinfo='percent+label',
                          textfont_size=14)
        fig.update_layout(showlegend=True, height=320,
                          margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(fig, use_container_width=True)

st.success("**인사이트:** 정기권 남성 66% vs 일일권 남성 61% — 두 권종 모두 남성 우세지만 일일권에서 여성 비중 상승. 일일권 여성 대상 감성 마케팅(🌸 동반 나들이 멘트)이 전환 유도에 효과적.")
st.divider()


# ── 섹션 3: 이용건수 비교 ────────────────────────────────
st.header("3. 권종별 전체 이용건수 비교")

col_bar, col_pie = st.columns([3,2])
with col_bar:
    df_bar = load("SELECT * FROM 이용건수집계")
    color_map = {'정기권':'#185FA5','일일권':'#1D9E75','기타':'#B4B2A9'}
    fig_bar = px.bar(
        df_bar.sort_values('이용건수합계', ascending=False),
        x='권종그룹', y='이용건수합계',
        color='권종그룹', color_discrete_map=color_map,
        text=df_bar.sort_values('이용건수합계',ascending=False)['이용건수합계'].apply(lambda x: f"{x/10000:.0f}만"),
        height=350, title='권종별 총 이용건수'
    )
    fig_bar.update_traces(textposition='outside', showlegend=False)
    fig_bar.update_layout(yaxis_title='이용건수', xaxis_title='',
                           margin=dict(l=0,r=0,t=40,b=0))
    st.plotly_chart(fig_bar, use_container_width=True)

with col_pie:
    fig_pie = px.pie(df_bar, values='이용건수합계', names='권종그룹',
                     color='권종그룹', color_discrete_map=color_map,
                     hole=0.5, height=350, title='비중')
    fig_pie.update_traces(textposition='inside', textinfo='percent+label', textfont_size=13)
    fig_pie.update_layout(showlegend=False, margin=dict(l=0,r=0,t=40,b=0))
    st.plotly_chart(fig_pie, use_container_width=True)

# 월별 추이
df_monthly = load("SELECT * FROM 월별집계 WHERE 권종그룹 != '기타'")
fig_line = px.line(
    df_monthly.sort_values('월'), x='월', y='이용건수합계',
    color='권종그룹', color_discrete_map={'정기권':'#185FA5','일일권':'#1D9E75'},
    markers=True, title='월별 이용건수 추이 (2025.07~12)',
    height=280
)
fig_line.update_layout(margin=dict(l=0,r=0,t=40,b=0), yaxis_title='이용건수', xaxis_title='')
st.plotly_chart(fig_line, use_container_width=True)

st.warning("**인사이트:** 정기권 이용건수 84% 점유 — 신규 유치보다 기존 정기권 이용자의 **이탈 방지(Churn Prevention)** 팝업이 비용 대비 효율 극대화.")
st.divider()


# ── 섹션 4: 연령대 분석 ──────────────────────────────────
st.header("4. 권종별 연령대 분포")

df_age = load("SELECT * FROM 연령대집계 WHERE 권종그룹 != '기타' AND 연령대코드 != '미상'")
age_order = ['~10대','20대','30대','40대','50대','60대','70대이상','기타']
df_age['연령대코드'] = pd.Categorical(df_age['연령대코드'], categories=age_order, ordered=True)
df_age = df_age.sort_values('연령대코드')
fig_age = px.bar(
    df_age, x='연령대코드', y='이용건수합계',
    color='권종그룹', barmode='group',
    color_discrete_map={'정기권':'#185FA5','일일권':'#1D9E75'},
    height=320, title='연령대별 권종 이용건수'
)
fig_age.update_layout(margin=dict(l=0,r=0,t=40,b=0), xaxis_title='', yaxis_title='이용건수')
st.plotly_chart(fig_age, use_container_width=True)
st.info("**인사이트:** 30~40대가 정기권의 핵심 이용층. 20대는 일일권 비중이 상대적으로 높아 **첫 이용→정기권 전환** 팝업 타이밍이 중요.")
st.divider()


# ── 섹션 5: 팝업광고 타겟팅 전략 ─────────────────────────
st.header("🎯 데이터 기반 팝업광고 타겟팅 전략")

df_target = load("SELECT 출처파트, 권종, 타겟, 발견_인사이트, 팝업_멘트, 광고_톤 FROM 팝업광고타겟팅")

# 필터
col_f1, col_f2 = st.columns([1,2])
with col_f1:
    filter_part = st.selectbox("출처 파트", ['전체'] + df_target['출처파트'].unique().tolist())
with col_f2:
    filter_grp = st.radio("권종", ['전체','정기권','일일권'], horizontal=True)

df_filtered = df_target.copy()
if filter_part != '전체':
    df_filtered = df_filtered[df_filtered['출처파트']==filter_part]
if filter_grp != '전체':
    df_filtered = df_filtered[df_filtered['권종']==filter_grp]

# 카드 형태로 출력
for _, row in df_filtered.iterrows():
    권종_color = '#E6F1FB' if row['권종']=='정기권' else '#E1F5EE'
    권종_text  = '#0C447C' if row['권종']=='정기권' else '#085041'
    with st.container():
        c1,c2 = st.columns([1,3])
        with c1:
            st.markdown(f"""
<div style='background:{권종_color};color:{권종_text};padding:6px 12px;border-radius:8px;font-size:13px;font-weight:600;display:inline-block'>{row['권종']}</div>
<div style='margin-top:6px;font-size:12px;color:#888'>{row['출처파트']} · {row['광고_톤']}</div>
<div style='margin-top:4px;font-size:13px;font-weight:600'>{row['타겟']}</div>
""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
<div style='background:#f8f9fa;border-left:3px solid {권종_text};padding:10px 14px;border-radius:0 8px 8px 0;margin-bottom:4px'>
  <div style='font-size:15px;font-weight:600;color:#1a1a1a'>💬 {row['팝업_멘트']}</div>
</div>
<div style='font-size:12px;color:#666;margin-top:4px'>📊 {row['발견_인사이트']}</div>
""", unsafe_allow_html=True)
        st.markdown("---")
