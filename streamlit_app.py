#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

#######################
# Page configuration
st.set_page_config(
    page_title="US Population Dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("default")

#######################
# CSS styling
#######################
# CSS styling
st.markdown("""
<style>

[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

[data-testid="stMetric"] {
    background-color: #f9f9f9;
    border-radius: 8px;
    text-align: center;
    padding: 15px 0;
    color: #000000;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    transform: translateX(-50%);
}

[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    transform: translateX(-50%);
}

</style>
""", unsafe_allow_html=True)



#######################
# Load data
df_reshaped = pd.read_csv('titanic.csv') ## 분석 데이터 넣기


#######################
# Sidebar
with st.sidebar:
    # ─────────────────────────────────────────────────────────
    # 앱 제목
    st.markdown("### 🚢 Titanic Survival Dashboard")
    st.caption("필터를 조정해 생존률 패턴을 탐색하세요.")
    st.markdown("---")

    # ─────────────────────────────────────────────────────────
    # 필터 위젯
    st.subheader("필터")

    # 성별
    sex_opts = sorted(df_reshaped["Sex"].dropna().unique().tolist())
    sex_sel = st.multiselect(
        "성별 (Sex)",
        options=sex_opts,
        default=sex_opts,
    )

    # 탑승 클래스
    pclass_labels = {1: "1등석", 2: "2등석", 3: "3등석"}
    pclass_sel = st.multiselect(
        "탑승 클래스 (Pclass)",
        options=[1, 2, 3],
        default=[1, 2, 3],
        format_func=lambda x: pclass_labels.get(x, x),
    )

    # 출항 항구
    embarked_labels = {"C": "Cherbourg (C)", "Q": "Queenstown (Q)", "S": "Southampton (S)"}
    embarked_all = [e for e in ["C", "Q", "S"] if e in df_reshaped["Embarked"].dropna().unique()]
    embarked_sel = st.multiselect(
        "출항 항구 (Embarked)",
        options=embarked_all,
        default=embarked_all,
        format_func=lambda x: embarked_labels.get(x, x),
    )

    # 나이 / 운임 범위
    age_min = int(df_reshaped["Age"].min(skipna=True)) if df_reshaped["Age"].notna().any() else 0
    age_max = int(df_reshaped["Age"].max(skipna=True)) if df_reshaped["Age"].notna().any() else 80
    age_include_na = st.toggle("나이 결측치 포함", value=True)
    age_range = st.slider("나이 범위 (Age)", min_value=age_min, max_value=age_max, value=(age_min, age_max))

    fare_min = float(df_reshaped["Fare"].min(skipna=True)) if df_reshaped["Fare"].notna().any() else 0.0
    fare_max = float(df_reshaped["Fare"].max(skipna=True)) if df_reshaped["Fare"].notna().any() else 600.0
    fare_range = st.slider("운임 범위 (Fare)", min_value=float(fare_min), max_value=float(fare_max), value=(float(fare_min), float(fare_max)))

    st.markdown("---")

    # 시각화 옵션 (테마/스케일 등)
    theme_sel = st.selectbox("색상 테마", ["blue", "green", "purple", "gray"], index=0)
    show_outliers = st.checkbox("운임 이상치 강조", value=False)

    # ─────────────────────────────────────────────────────────
    # 필터 적용
    df_filtered = df_reshaped.copy()

    if sex_sel:
        df_filtered = df_filtered[df_filtered["Sex"].isin(sex_sel)]

    if pclass_sel:
        df_filtered = df_filtered[df_filtered["Pclass"].isin(pclass_sel)]

    if embarked_sel:
        df_filtered = df_filtered[df_filtered["Embarked"].isin(embarked_sel)]

    # 나이 필터 (결측 포함 옵션)
    if age_include_na:
        df_filtered = df_filtered[(df_filtered["Age"].between(age_range[0], age_range[1])) | (df_filtered["Age"].isna())]
    else:
        df_filtered = df_filtered[df_filtered["Age"].between(age_range[0], age_range[1])]

    # 운임 필터
    df_filtered = df_filtered[df_filtered["Fare"].between(fare_range[0], fare_range[1])]

    # ─────────────────────────────────────────────────────────
    # 현재 선택 상태 요약
    st.subheader("선택 요약")
    st.metric("필터 적용된 승객 수", len(df_filtered))
    st.caption(
        f"성별: {', '.join(sex_sel) if sex_sel else '전체'} | "
        f"Pclass: {', '.join(pclass_labels[p] for p in pclass_sel) if pclass_sel else '전체'} | "
        f"Embarked: {', '.join(embarked_labels[e] for e in embarked_sel) if embarked_sel else '전체'}"
    )

    # 다른 영역에서 사용할 수 있도록 세션에 저장
    st.session_state["theme"] = theme_sel
    st.session_state["show_outliers"] = show_outliers
    st.session_state["df_filtered"] = df_filtered



#######################
# Plots



#######################
# Dashboard Main Panel
col = st.columns((1.5, 4.5, 2), gap='medium')

with col[0]:
    st.markdown("## 📊 핵심 요약 지표")

    df_filtered = st.session_state["df_filtered"]

    # ───────────────────────────────
    # 전체 생존/사망자 수
    survived_count = int(df_filtered["Survived"].sum())
    dead_count = int((df_filtered["Survived"] == 0).sum())
    total_count = len(df_filtered)
    survival_rate = (survived_count / total_count * 100) if total_count > 0 else 0

    st.metric("생존자 수", f"{survived_count:,}", delta=f"{survival_rate:.1f}%")
    st.metric("사망자 수", f"{dead_count:,}", delta=f"-{100 - survival_rate:.1f}%")

    st.markdown("---")

    # ───────────────────────────────
    # 클래스별 생존률
    st.markdown("### 🎟 클래스별 생존률")
    class_survival = (
        df_filtered.groupby("Pclass")["Survived"]
        .mean()
        .reset_index()
        .sort_values("Pclass")
    )

    # 시각화 (Altair)
    chart_class = (
        alt.Chart(class_survival)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=alt.X("Pclass:O", title="탑승 클래스"),
            y=alt.Y("Survived:Q", title="생존률", axis=alt.Axis(format="%")),
            color=alt.Color("Pclass:O", legend=None),
            tooltip=["Pclass", alt.Tooltip("Survived", format=".0%")],
        )
        .properties(height=250)
    )
    st.altair_chart(chart_class, use_container_width=True)

    st.caption("※ 생존률 = 각 클래스의 생존자 수 ÷ 해당 클래스 총 인원")



with col[1]:
    st.markdown("## 📍 분포 & 히트맵 시각화")

    df_filtered = st.session_state.get("df_filtered", None)
    theme = st.session_state.get("theme", "blue")
    show_outliers = st.session_state.get("show_outliers", False)

    if df_filtered is None or df_filtered.empty:
        st.info("선택된 조건에 해당하는 데이터가 없습니다. 사이드바 필터를 조정해 보세요.")
    else:
        # ─────────────────────────────────────────────
        # 1) 나이 분포: 생존 여부 비교 (히스토그램)
        st.markdown("### 🧒 Age 분포 (생존 여부 비교)")
        df_age = df_filtered.dropna(subset=["Age"]).copy()
        if df_age.empty:
            st.warning("나이(Age)가 있는 데이터가 부족합니다.")
        else:
            fig_age = px.histogram(
                df_age,
                x="Age",
                nbins=30,
                color=df_age["Survived"].map({0: "Died", 1: "Survived"}),
                barmode="overlay",
                opacity=0.65,
                labels={"color": "Survival"},
                title=None,
            )
            fig_age.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=300)
            st.plotly_chart(fig_age, use_container_width=True)

        st.markdown("---")

        # ─────────────────────────────────────────────  
        # 2) 운임(Fare) 분포: 클래스/생존 여부 (박스플롯)
        st.markdown("### 💴 Fare 분포 (클래스 × 생존)")
        df_fare = df_filtered.dropna(subset=["Fare"]).copy()
        if df_fare.empty:
            st.warning("운임(Fare) 데이터가 부족합니다.")
        else:
            df_fare["Survival"] = df_fare["Survived"].map({0: "Died", 1: "Survived"})
            fig_fare = px.box(
                df_fare,
                x="Pclass",
                y="Fare",
                color="Survival",
                points="all" if show_outliers else False,
                labels={"Pclass": "Class", "Fare": "Fare"},
                title=None,
            )
            fig_fare.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=300)
            st.plotly_chart(fig_fare, use_container_width=True)

        st.markdown("---")

        # ─────────────────────────────────────────────
        # 3) 히트맵: 연령대 × 클래스별 평균 생존률
        st.markdown("### 🔥 연령대 × 클래스 히트맵 (평균 생존률)")
        import numpy as np
        tmp = df_filtered.copy()
        # 연령대 구간화
        tmp["AgeBin"] = pd.cut(tmp["Age"], bins=[0, 10, 20, 30, 40, 50, 60, 80], right=False)
        hm = (
            tmp.dropna(subset=["AgeBin"])
               .groupby(["AgeBin", "Pclass"])["Survived"]
               .mean()
               .reset_index()
        )
        # Altair 히트맵
        heat = (
            alt.Chart(hm)
            .mark_rect()
            .encode(
                x=alt.X("Pclass:O", title="Class"),
                y=alt.Y("AgeBin:O", title="Age band"),
                color=alt.Color("Survived:Q", title="Survival Rate", scale=alt.Scale(domain=[0, 1])),
                tooltip=[
                    alt.Tooltip("AgeBin:O", title="Age band"),
                    alt.Tooltip("Pclass:O", title="Class"),
                    alt.Tooltip("Survived:Q", title="Rate", format=".1%"),
                ],
            )
            .properties(height=260)
        )
        st.altair_chart(heat, use_container_width=True)

        st.caption("※ 셀 값은 해당 연령대·클래스의 평균 생존률입니다.")

        st.markdown("---")

        # ─────────────────────────────────────────────
        # 4) Pclass × Embarked 생존률 피벗 테이블
        st.markdown("### 📑 Pclass × Embarked 생존률 테이블")
        tbl = (
            df_filtered.dropna(subset=["Embarked"])
            .assign(Embarked=df_filtered["Embarked"].map({"C": "C", "Q": "Q", "S": "S"}))
            .pivot_table(values="Survived", index="Pclass", columns="Embarked", aggfunc="mean")
            .reindex(index=[1, 2, 3])
        )
        # 퍼센트 포맷으로 보기 좋게
        tbl_disp = (tbl * 100).round(1)
        st.dataframe(tbl_disp, use_container_width=True)






with col[2]:
    st.markdown("## 🏅 Top Groups & 정보")

    df_filtered = st.session_state.get("df_filtered", None)
    if df_filtered is None or df_filtered.empty:
        st.info("선택된 조건에 해당하는 데이터가 없습니다.")
    else:
        # ─────────────────────────────────────────────
        # 1) 탑승 항구별 생존자 수 Top
        st.markdown("### ⛴️ 탑승 항구별 생존자 수")
        embarked_counts = (
            df_filtered[df_filtered["Survived"] == 1]
            .groupby("Embarked")["PassengerId"]
            .count()
            .reset_index()
            .rename(columns={"PassengerId": "Survivors"})
            .sort_values("Survivors", ascending=False)
        )
        if not embarked_counts.empty:
            fig_embarked = px.bar(
                embarked_counts,
                x="Survivors",
                y="Embarked",
                orientation="h",
                text="Survivors",
                color="Embarked",
                title=None,
            )
            fig_embarked.update_traces(textposition="outside")
            fig_embarked.update_layout(
                margin=dict(l=0, r=0, t=10, b=0), height=250, showlegend=False
            )
            st.plotly_chart(fig_embarked, use_container_width=True)
        else:
            st.warning("탑승 항구별 생존자 데이터가 없습니다.")

        st.markdown("---")

        # ─────────────────────────────────────────────
        # 2) 성별 × 클래스 조합: 생존률 Top
        st.markdown("### 👥 성별 × 클래스 생존률")
        sex_class = (
            df_filtered.groupby(["Sex", "Pclass"])["Survived"]
            .mean()
            .reset_index()
            .sort_values("Survived", ascending=False)
        )
        if not sex_class.empty:
            top_rows = sex_class.head(5)
            st.table(
                top_rows.rename(
                    columns={
                        "Sex": "성별",
                        "Pclass": "클래스",
                        "Survived": "생존률",
                    }
                ).assign(생존률=lambda d: (d["생존률"] * 100).round(1).astype(str) + "%")
            )
        else:
            st.warning("성별 × 클래스 조합 데이터가 없습니다.")

        st.markdown("---")

        # ─────────────────────────────────────────────
        # 3) 상위 이름(가문) 예시 – 생존자 많이 속한 성
        st.markdown("### 🧾 생존자 다수 포함 성씨 Top 5")
        df_filtered["LastName"] = df_filtered["Name"].str.split(",").str[0]
        last_counts = (
            df_filtered[df_filtered["Survived"] == 1]
            .groupby("LastName")["PassengerId"]
            .count()
            .reset_index()
            .rename(columns={"PassengerId": "Survivors"})
            .sort_values("Survivors", ascending=False)
            .head(5)
        )
        if not last_counts.empty:
            st.dataframe(last_counts, use_container_width=True)
        else:
            st.warning("생존자 성씨 데이터가 부족합니다.")

    st.markdown("---")

    # ─────────────────────────────────────────────
    # 4) About Section
    st.markdown("## ℹ️ About Dataset")
    st.write(
        """
        - **데이터 출처**: [Kaggle Titanic Dataset](https://www.kaggle.com/c/titanic)
        - **컬럼 설명**:
            - *Survived*: 생존 여부 (1 = 생존, 0 = 사망)  
            - *Pclass*: 티켓 클래스 (1 = 상류, 2 = 중류, 3 = 하류)  
            - *Sex*: 성별  
            - *Age*: 나이 (일부 결측치 존재)  
            - *SibSp*: 함께 탑승한 형제/배우자 수  
            - *Parch*: 함께 탑승한 부모/자녀 수  
            - *Ticket*: 티켓 번호  
            - *Fare*: 요금  
            - *Cabin*: 선실 번호 (결측치 많음)  
            - *Embarked*: 탑승 항구 (C = Cherbourg, Q = Queenstown, S = Southampton)  
        """
    )
