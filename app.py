import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client

# --- 1. Supabase 데이터베이스 연결 설정 ---
@st.cache_resource
def init_connection():
    # Streamlit Secrets에 저장된 정보를 안전하게 가져옵니다.
    url = st.secrets["https://jdhndixdhiglmelaeglt.supabase.co"]
    key = st.secrets["sb_publishable_6IzSc6-QfR8cWze-7PUyRA_E4wc17bM"]
    return create_client(url, key)

try:
    supabase: Client = init_connection()
except Exception as e:
    st.error("Supabase 연결 설정에 실패했습니다. 스트림릿 Secrets 설정을 확인해주세요.")

# --- 2. 데이터 불러오기 공통 함수 ---
def load_data():
    try:
        # student_survey 테이블에서 id 순으로 데이터를 가져옵니다.
        response = supabase.table("student_survey").select("*").order("id").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# 최신 데이터 로드
df = load_data()

# --- 3. UI 및 메뉴 레이아웃 설정 ---
st.set_page_config(page_title="학생 생활습관 설문 앱", layout="wide")

st.title("📘 학생 생활습관 설문 웹앱")
st.caption("설문을 입력하고 제출하면 Supabase 데이터베이스에 자동으로 저장됩니다.")

# 사이드바 메뉴 구성
menu = st.sidebar.radio("메뉴 선택", ["📝 설문하기", "📊 분석 확인하기"])

# =========================================================================
# --- [메뉴 1: 설문하기] ---
# =========================================================================
if menu == "📝 설문하기":
    st.header("1. 설문 입력하기")
    
    # 🆔 자동 학생 ID 생성 로직 (마지막 ID를 기반으로 s_XXX 형식 부여)
    if not df.empty and 'id' in df.columns:
        last_id = df['id'].max()  # 예: 's_019'
        try:
            last_num = int(last_id.split('_')[1])
            new_id = f"s_{last_num + 1:03d}"  # 예: 's_020'
        except:
            new_id = f"s_{len(df) + 1:03d}"
    else:
        new_id = "s_001"
        
    st.info(f"💡 자동 생성 학생 ID : **{new_id}**")
    
    # 설문 입력 폼 시작
    with st.form("survey_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            grade_class = st.selectbox("반", [f"1-{i}" for i in range(1, 11)])
            sleep_hours = st.number_input("수면시간 (시간)", min_value=0.0, max_value=24.0, value=6.0, step=0.5)
            phone_hours = st.number_input("스마트폰 사용시간 (시간)", min_value=0.0, max_value=24.0, value=3.0, step=0.5)
            breakfast = st.radio("아침식사 여부", ["YES", "NO"], index=0)
            
        with col2:
            commute_minutes = st.number_input("통학시간(분)", min_value=0, max_value=300, value=30, step=5)
            tired_score = st.select_slider("피곤함 점수 (1 = 전혀 피곤하지 않음, 5 = 매우 피곤함)", options=[1, 2, 3, 4, 5], value=3)
            focus_score = st.select_slider("집중도 점수 (1 = 집중이 잘 안 됨, 5 = 매우 잘 집중됨)", options=[1, 2, 3, 4, 5], value=3)
            favorite_subject = st.selectbox("좋아하는 과목", ["국어", "수학", "영어", "과학", "사회", "체육", "음악", "미술", "정보"])
            
        submit_btn = st.form_submit_button("설문 제출하기")
        
        if submit_btn:
            # 수파베이스 DB 컬럼 양식에 맞추어 데이터 매핑
            new_data = {
                "id": new_id,
                "grade_class": grade_class,
                "sleep_hours": float(sleep_hours),
                "phone_hours": float(phone_hours),
                "breakfast": breakfast,
                "commute_minutes": int(commute_minutes),
                "tired_score": int(tired_score),
                "focus_score": int(focus_score),
                "favorite_subject": favorite_subject
            }
            
            try:
                # 테이블에 삽입 실행
                supabase.table("student_survey").insert(new_data).execute()
                st.success(f"🎉 {new_id} 학생의 설문이 수파베이스에 성공적으로 저장되었습니다!")
                st.balloons()
                # 저장 후 즉시 최신 데이터를 반영하기 위해 앱 리런(Rerun)
                st.rerun()
            except Exception as e:
                st.error(f"제출 실패! 오류 발생: {e}")

# =========================================================================
# --- [메뉴 2: 분석 확인하기] ---
# =========================================================================
elif menu == "📊 분석 확인하기":
    st.header("2. 분석 확인하기")
    
    if df.empty:
        st.warning("데이터베이스에 분석할 데이터가 없습니다. 먼저 설문을 진행해 주세요.")
    else:
        # 📌 2-1. 전체 설문 요약 (KPI 대시보드)
        st.subheader("📌 전체 설문 요약")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        total_students = len(df)
        avg_sleep = df['sleep_hours'].mean()
        avg_phone = df['phone_hours'].mean()
        avg_focus = df['focus_score'].mean()
        
        kpi1.metric("참여 학생 수", f"{total_students}명")
        kpi2.metric("평균 수면시간", f"{avg_sleep:.1f}시간")
        kpi3.metric("평균 스마트폰 사용", f"{avg_phone:.1f}시간")
        kpi4.metric("평균 집중도", f"{avg_focus:.1f}점")
        
        st.markdown("---")
        
        # 👤 2-2. 나와 친구들 평균 비교하기
        st.subheader("👤 나와 친구들 평균 비교하기")
        selected_id = st.selectbox("내 학생 ID를 선택하세요.", df['id'].tolist(), index=len(df)-1)
        
        # 선택한 학생 데이터 가공 및 전체 평균과 비교
        my_data = df[df['id'] == selected_id].iloc[0]
        
        metrics_list = ["수면시간", "스마트폰 사용시간", "집중도점수", "통학시간", "피곤함점수"]
        my_scores = [
            my_data['sleep_hours'], 
            my_data['phone_hours'], 
            my_data['focus_score'], 
            my_data['commute_minutes'],
            my_data['tired_score']
        ]
        avg_scores = [
            df['sleep_hours'].mean(),
            df['phone_hours'].mean(),
            df['focus_score'].mean(),
            df['commute_minutes'].mean(),
            df['tired_score'].mean()
        ]
        
        # 비교 멀티 바 차트 생성
        fig_compare = go.Figure()
        fig_compare.add_trace(go.Bar(x=metrics_list, y=my_scores, name='나', marker_color='#11CAA0'))
        fig_compare.add_trace(go.Bar(x=metrics_list, y=avg_scores, name='전체 평균', marker_color='#005088'))
        fig_compare.update_layout(barmode='group', height=400, margin=dict(t=20, b=20))
        st.plotly_chart(fig_compare, use_container_width=True)
        
        # 🧠 간단 해석 결과 출력
        st.subheader("🧠 간단 해석")
        
        def generate_insight(my_val, avg_val, title):
            diff = my_val - avg_val
            if title == "집중도":
                state = "높습니다" if diff > 0 else "낮습니다" if diff < 0 else "평균 수준입니다"
            else:
                state = "많습니다" if diff > 0 else "적습니다" if diff < 0 else "평균 수준입니다"
            return f"{selected_id} 학생의 {title}은(는) 전체 평균보다 {state}."

        st.info(f"""
        💡 **{selected_id} 학생 맞춤형 분석 결과**
        * {generate_insight(my_data['sleep_hours'], avg_sleep, '수면시간')}
        * {generate_insight(my_data['phone_hours'], avg_phone, '스마트폰 사용시간')}
        * {generate_insight(my_data['focus_score'], avg_focus, '집중도')}
        """)
        
        st.markdown("---")
        
        # 하단 시각화 그래프 배치 (좌우 2열 배치)
        col_left, col_right = st.columns(2)
        
        with col_left:
            # 🏫 반별 평균 집중도
            st.subheader("🏫 반별 평균 집중도")
            df_class_focus = df.groupby('grade_class')['focus_score'].mean().reset_index().sort_values(by='grade_class')
            fig_class = px.bar(df_class_focus, x='grade_class', y='focus_score', 
                               labels={'grade_class': '반', 'focus_score': '평균 집중도'},
                               color_discrete_sequence=['#005088'])
            fig_class.update_yaxis(range=[0, 5])
            st.plotly_chart(fig_class, use_container_width=True)
            st.caption("각 반의 평균 집중도 점수를 비교한 그래프입니다.")
            
            # 🍚 아침식사 여부별 평균 피곤함 점수
            st.subheader("🍚 아침식사 여부별 평균 피곤함 점수")
            df_bf_tired = df.groupby('breakfast')['tired_score'].mean().reset_index()
            fig_bf = px.bar(df_bf_tired, x='breakfast', y='tired_score',
                            labels={'breakfast': '아침식사 여부', 'tired_score': '평균 피곤함'},
                            color='breakfast', color_discrete_map={'YES': '#11CAA0', 'NO': '#ef4444'})
            fig_bf.update_yaxis(range=[0, 5])
            st.plotly_chart(fig_bf, use_container_width=True)
            st.caption("아침식사를 한 학생과 하지 않은 학생의 평균 피곤함 점수를 비교합니다.")
            
        with col_right:
            # 😴 수면시간과 집중도 관계 (산점도 + 추세선)
            st.subheader("😴 수면시간과 집중도 관계")
            fig_scatter = px.scatter(df, x='sleep_hours', y='focus_score', 
                                     labels={'sleep_hours': 'sleep_hours', 'focus_score': 'focus_score'},
                                     color_discrete_sequence=['#005088'])
            fig_scatter.update_xaxis(range=[0, 10])
            fig_scatter.update_yaxis(range=[0, 6])
            st.plotly_chart(fig_scatter, use_container_width=True)
            st.caption("점 하나는 학생 한 명을 의미합니다. 오른쪽으로 갈수록 수면시간이 많고, 위로 갈수록 집중도 점수가 높습니다.")
            
            # 📚 좋아하는 과목별 평균 집중도
            st.subheader("📚 좋아하는 과목별 평균 집중도")
            df_sub_focus = df.groupby('favorite_subject')['focus_score'].mean().reset_index().sort_values(by='focus_score', ascending=False)
            fig_sub = px.bar(df_sub_focus, x='favorite_subject', y='focus_score',
                             labels={'favorite_subject': '좋아하는 과목', 'focus_score': '평균 집중도'},
                             color_discrete_sequence=['#11CAA0'])
            fig_sub.update_yaxis(range=[0, 5])
            st.plotly_chart(fig_sub, use_container_width=True)
            st.caption("좋아하는 과목에 따라 평균 집중도 점수가 어떻게 다른지 확인합니다.")

        st.markdown("---")
        
        # 📋 원본 데이터 보기
        st.subheader("📋 원본 데이터 보기")
        # 정렬 및 불필요한 날짜 컬럼 제외 후 출력
        df_display = df.drop(columns=['created_at'], errors='ignore')
        st.dataframe(df_display, use_container_width=True)
