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
    background-color: #393939;
    text-align: center;
    padding: 15px 0;
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

</style>
""", unsafe_allow_html=True)


#######################
# Load data

df_reshaped = pd.read_csv(
    '20231231.csv',
    encoding='cp949'
)

#######################
# Sidebar
with st.sidebar:
# 대시보드 제목
    st.markdown("### 🇰🇷 범죄 통계 대시보드")
    st.caption("경찰청 범죄 발생 지역별 통계 (기준일: 2023-12-31)")

    st.markdown("---")

    # =========================
    # 1) 범죄 유형 선택
    # =========================
    # 범죄 대분류 선택
    if "범죄대분류" in df_reshaped.columns:
        crime_main_options = sorted(df_reshaped["범죄대분류"].dropna().unique())
        selected_crime_main = st.selectbox(
            "범죄 대분류 선택",
            options=crime_main_options,
            index=0 if len(crime_main_options) > 0 else None,
        )
    else:
        selected_crime_main = None
        st.warning("⚠️ '범죄대분류' 컬럼을 찾을 수 없습니다. 원본 데이터를 확인해 주세요.")

    # 범죄 중분류 선택 (대분류 선택에 따라 동적 생성)
    if selected_crime_main is not None and "범죄중분류" in df_reshaped.columns:
        sub_mask = df_reshaped["범죄대분류"] == selected_crime_main
        sub_options = sorted(df_reshaped.loc[sub_mask, "범죄중분류"].dropna().unique())
        crime_sub_options = ["전체"] + sub_options
        selected_crime_sub = st.selectbox(
            "범죄 중분류 선택",
            options=crime_sub_options,
            index=0,
        )
    else:
        selected_crime_sub = "전체"

    st.markdown("---")

    # =========================
    # 2) 지역(시도) 선택
    # =========================
    # 가정: 앞의 두 컬럼(범죄대분류, 범죄중분류)을 제외한 나머지 컬럼명이 지역
    if len(df_reshaped.columns) > 2:
        region_cols = df_reshaped.columns[2:]
        selected_regions = st.multiselect(
            "분석 대상 지역(시도) 선택",
            options=region_cols.tolist(),
            default=region_cols.tolist(),  # 기본은 전체 선택
        )
    else:
        selected_regions = []
        st.warning("⚠️ 지역(시도) 컬럼이 충분하지 않습니다.")

    st.markdown("---")

    # =========================
    # 3) 시각화 / 대시보드 옵션
    # =========================
    color_theme = st.selectbox(
        "색상 테마 선택",
        options=["기본(default)", "파랑 계열", "초록 계열", "붉은 계열"],
        index=0,
    )

    top_n = st.slider(
        "우측 Top 지역 개수",
        min_value=5,
        max_value=30,
        value=10,
        step=1,
    )

    st.markdown("---")

    # =========================
    # 4) 머신러닝 분석 옵션
    # =========================
    ml_method = st.selectbox(
        "머신러닝 분석 방법 선택",
        options=[
            "군집 분석 (Clustering)",
            "회귀 분석 (Regression)",
            "분류 분석 (Classification)",
            "사용 안 함",
        ],
        index=0,
        help="대시보드 본문에서 적용할 분석 방법을 선택합니다.",
    )

    # 선택 값들을 session_state에 저장해 두면,
    # 아래 메인 패널/그래프 영역에서 재사용하기 편리합니다.
    st.session_state["selected_crime_main"] = selected_crime_main
    st.session_state["selected_crime_sub"] = selected_crime_sub
    st.session_state["selected_regions"] = selected_regions
    st.session_state["color_theme"] = color_theme
    st.session_state["top_n"] = top_n
    st.session_state["ml_method"] = ml_method

#######################
# Plots



#######################
# Dashboard Main Panel
col = st.columns((1.5, 4.5, 2), gap='medium')

with col[0]:
    st.markdown("### 📊 요약 지표")

    # ---- 사이드바에서 선택한 값 불러오기 ----
    crime_main = st.session_state.get("selected_crime_main", None)
    crime_sub = st.session_state.get("selected_crime_sub", "전체")
    selected_regions = st.session_state.get(
        "selected_regions",
        df_reshaped.columns[2:]  # 기본: 모든 지역
    )
    top_n = st.session_state.get("top_n", 10)

    # ---- 기본 컬럼 정의 ----
    # 앞의 두 컬럼(범죄대분류, 범죄중분류) 제외 = 지역 컬럼으로 가정
    all_region_cols = df_reshaped.columns[2:]
    # 선택된 지역 중 실제로 존재하는 컬럼만 사용
    region_cols = [c for c in all_region_cols if c in selected_regions]

    # 안전장치: 지역이 하나도 선택 안 된 경우
    if len(region_cols) == 0:
        st.warning("분석 대상 지역이 선택되지 않았습니다. 사이드바에서 지역을 선택해 주세요.")
    else:
        # ---- 총합 계산 ----
        # 1) 전체 범죄 (모든 유형, 모든 지역)
        total_all_crime = int(df_reshaped[all_region_cols].sum().sum())

        # 2) 선택한 대분류 전체
        if crime_main is not None and "범죄대분류" in df_reshaped.columns:
            main_mask = df_reshaped["범죄대분류"] == crime_main
            df_main = df_reshaped[main_mask]
            total_main_crime = int(df_main[all_region_cols].sum().sum())
        else:
            df_main = df_reshaped.copy()
            total_main_crime = int(df_main[all_region_cols].sum().sum())

        # 3) 선택한 (대분류 + 중분류 or 대분류 전체)
        if (
            crime_sub != "전체"
            and "범죄중분류" in df_reshaped.columns
            and crime_main is not None
        ):
            sub_mask = (df_reshaped["범죄대분류"] == crime_main) & (
                df_reshaped["범죄중분류"] == crime_sub
            )
            df_selected = df_reshaped[sub_mask]
        else:
            # 중분류 "전체"면 대분류만 필터
            df_selected = df_main

        total_selected_crime = int(df_selected[all_region_cols].sum().sum())

        # ---- Metric 3개 표시 ----
        mcol1, mcol2 = st.columns(2)

        with mcol1:
            st.metric(
                label="전체 범죄 발생 (전국)",
                value=f"{total_all_crime:,} 건",
            )
            st.metric(
                label=f"{crime_main} 전체" if crime_main else "선택 대분류 전체",
                value=f"{total_main_crime:,} 건",
            )

        with mcol2:
            label_selected = (
                f"{crime_main} - {crime_sub}"
                if (crime_main is not None and crime_sub != '전체')
                else (f"{crime_main} (대분류 전체)" if crime_main else "선택 범죄")
            )
            st.metric(
                label=label_selected,
                value=f"{total_selected_crime:,} 건",
            )

        st.markdown("---")

        # ---- 도넛 1: 전체 범죄 대비 선택 범죄 비중 ----
        st.markdown("#### 전체 범죄 대비 선택 범죄 비중")

        if total_all_crime > 0 and total_selected_crime > 0:
            share_selected = total_selected_crime / total_all_crime
            others = total_all_crime - total_selected_crime

            fig_share = px.pie(
                values=[total_selected_crime, others],
                names=["선택 범죄", "기타 범죄"],
                hole=0.6,
            )
            fig_share.update_traces(textposition="inside", textinfo="label+percent")
            fig_share.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=260,
                showlegend=False,
            )
            st.plotly_chart(fig_share, use_container_width=True)
        else:
            st.info("선택한 조건에서 유효한 데이터가 없습니다.")

        st.markdown("#### 상위 지역 집중도 (선택 범죄 기준)")

        # ---- 도넛 2: 선택 범죄 중 상위 Top N 지역 집중도 ----
        # 지역별 합계 (선택된 범죄만)
        region_sums = df_selected[all_region_cols].sum()

        # 총 선택 범죄와 일치하도록 보정
        total_selected_from_regions = int(region_sums.sum())

        if total_selected_from_regions > 0:
            region_sums_sorted = region_sums.sort_values(ascending=False)
            top_n_effective = min(top_n, len(region_sums_sorted))
            top_sum = int(region_sums_sorted.head(top_n_effective).sum())
            others_sum = total_selected_from_regions - top_sum

            fig_top = px.pie(
                values=[top_sum, others_sum],
                names=[f"상위 {top_n_effective} 지역", "기타 지역"],
                hole=0.6,
            )
            fig_top.update_traces(textposition="inside", textinfo="label+percent")
            fig_top.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=260,
                showlegend=False,
            )
            st.plotly_chart(fig_top, use_container_width=True)
        else:
            st.info("선택한 범죄 유형에 해당하는 지역별 데이터가 없습니다.")


with col[1]:
    st.markdown("### 🗺 시도별 범죄 현황")

    # ---- 사이드바에서 선택한 값 불러오기 ----
    crime_main = st.session_state.get("selected_crime_main", None)
    crime_sub = st.session_state.get("selected_crime_sub", "전체")
    selected_regions = st.session_state.get(
        "selected_regions",
        df_reshaped.columns[2:]  # 기본값: 모든 지역
    )

    # 앞의 두 컬럼(범죄대분류, 범죄중분류)을 제외한 나머지를 지역 컬럼으로 가정
    all_region_cols = df_reshaped.columns[2:]
    region_cols = [c for c in all_region_cols if c in selected_regions]

    if len(region_cols) == 0:
        st.warning("분석 대상 지역(시도)이 선택되지 않았습니다. 사이드바에서 지역을 하나 이상 선택해 주세요.")
    else:
        # ==============================
        # 1) 선택 조건에 따른 데이터 필터링
        # ==============================
        df_filtered = df_reshaped.copy()

        # (1) 대분류 필터
        if crime_main is not None and "범죄대분류" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["범죄대분류"] == crime_main]

        # (2) 중분류 필터
        if (
            crime_sub != "전체"
            and "범죄중분류" in df_filtered.columns
        ):
            df_filtered = df_filtered[df_filtered["범죄중분류"] == crime_sub]

        # ==============================
        # 2) 시도별 발생 건수 막대 그래프
        # ==============================
        st.markdown("#### 시도별 발생 건수 (선택 범죄 기준)")

        # 시도별 합계 계산
        region_sums = df_filtered[region_cols].sum()
        region_df = region_sums.reset_index()
        region_df.columns = ["지역", "발생건수"]

        if region_df["발생건수"].sum() == 0:
            st.info("선택하신 조건에 해당하는 시도별 발생 건수가 없습니다.")
        else:
            region_df_sorted = region_df.sort_values("발생건수", ascending=False)

            fig_region = px.bar(
                region_df_sorted,
                x="지역",
                y="발생건수",
                labels={"지역": "시도", "발생건수": "발생 건수(건)"},
                text="발생건수",
            )
            fig_region.update_traces(texttemplate="%{text:,}건", textposition="outside")
            fig_region.update_layout(
                xaxis_tickangle=-45,
                margin=dict(l=10, r=10, t=10, b=60),
                height=320,
            )
            st.plotly_chart(fig_region, use_container_width=True)

        st.markdown("---")

        # ==============================
        # 3) 범죄중분류 × 시도 히트맵
        # ==============================
        st.markdown("#### 범죄 유형 vs 시도 히트맵")

        # 히트맵은 '선택한 대분류' 기준으로, 여러 중분류를 한 번에 비교
        if crime_main is not None and "범죄대분류" in df_reshaped.columns:
            heat_df = df_reshaped[df_reshaped["범죄대분류"] == crime_main].copy()
        else:
            heat_df = df_reshaped.copy()

        # 필요한 컬럼만 사용
        if "범죄중분류" in heat_df.columns:
            heat_df = heat_df[["범죄중분류"] + list(region_cols)].copy()
            heat_df = heat_df.set_index("범죄중분류")
        else:
            heat_df = pd.DataFrame()

        if heat_df.empty:
            st.info("히트맵을 구성할 수 있는 데이터가 없습니다.")
        else:
            fig_heat = px.imshow(
                heat_df,
                aspect="auto",
                labels=dict(x="시도", y="범죄중분류", color="발생 건수"),
            )
            fig_heat.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=380,
            )
            st.plotly_chart(fig_heat, use_container_width=True)




with col[2]:
    st.markdown("### 🏆 Top 지역 & 머신러닝 분석")

    # ---- 사이드바에서 선택한 값 불러오기 ----
    crime_main = st.session_state.get("selected_crime_main", None)
    crime_sub = st.session_state.get("selected_crime_sub", "전체")
    selected_regions = st.session_state.get(
        "selected_regions",
        df_reshaped.columns[2:]  # 기본값: 모든 지역
    )
    top_n = st.session_state.get("top_n", 10)
    ml_method = st.session_state.get("ml_method", "사용 안 함")

    # 지역 컬럼 정의
    all_region_cols = df_reshaped.columns[2:]
    region_cols = [c for c in all_region_cols if c in selected_regions]

    if len(region_cols) == 0:
        st.warning("분석 대상 지역(시도)이 선택되지 않았습니다. 사이드바에서 지역을 하나 이상 선택해 주세요.")
    else:
        # ======================================================
        # 1) 선택 조건에 따른 데이터 필터링 (대분류 / 중분류)
        # ======================================================
        df_filtered = df_reshaped.copy()

        # (1) 대분류 필터
        if crime_main is not None and "범죄대분류" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["범죄대분류"] == crime_main]

        # (2) 중분류 필터
        if (
            crime_sub != "전체"
            and "범죄중분류" in df_filtered.columns
        ):
            df_filtered = df_filtered[df_filtered["범죄중분류"] == crime_sub]

        # ======================================================
        # 2) Top N 지역 막대 그래프 + 테이블
        # ======================================================
        st.markdown("#### Top 지역 (선택 범죄 기준)")

        region_sums = df_filtered[region_cols].sum()
        region_df = region_sums.reset_index()
        region_df.columns = ["지역", "발생건수"]

        if region_df["발생건수"].sum() == 0:
            st.info("선택하신 조건에 해당하는 지역별 발생 건수가 없습니다.")
        else:
            region_df_sorted = region_df.sort_values("발생건수", ascending=False)
            top_n_effective = min(top_n, len(region_df_sorted))
            top_df = region_df_sorted.head(top_n_effective)

            # 가로 막대 그래프
            fig_top = px.bar(
                top_df.sort_values("발생건수"),  # 아래에서 위로 오르게 정렬
                x="발생건수",
                y="지역",
                orientation="h",
                labels={"지역": "시도", "발생건수": "발생 건수(건)"},
                text="발생건수",
            )
            fig_top.update_traces(texttemplate="%{text:,}건", textposition="outside")
            fig_top.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=320,
            )
            st.plotly_chart(fig_top, use_container_width=True)

            # Top 지역 테이블
            st.markdown("#### Top 지역 상세 데이터")
            st.dataframe(
                top_df.assign(발생건수=top_df["발생건수"].astype(int)).style.format(
                    {"발생건수": "{:,}"}
                ),
                use_container_width=True,
                height=230,
            )

        st.markdown("---")

        # ======================================================
        # 3) 머신러닝 분석 (군집 분석 중심)
        # ======================================================
        st.markdown("### 🤖 머신러닝 분석 결과")

        if ml_method == "사용 안 함":
            st.info("사이드바에서 머신러닝 분석 방법을 선택하면 추가 인사이트가 표시됩니다.")
        elif ml_method in ["회귀 분석 (Regression)", "분류 분석 (Classification)"]:
            st.info(
                "현재 데이터 구조(단일 시점, 지역별 단일 값)를 고려하여 "
                "**이 버전 대시보드에서는 군집 분석(Clustering)만 지원**합니다.\n\n"
                "사이드바에서 **'군집 분석 (Clustering)'**을 선택해 주세요."
            )
        elif ml_method == "군집 분석 (Clustering)":
            # ------------------------
            # 군집 분석 수행
            # ------------------------
            try:
                from sklearn.cluster import KMeans
                from sklearn.preprocessing import StandardScaler
                sklearn_available = True
            except ImportError:
                sklearn_available = False
                st.error(
                    "`scikit-learn` 라이브러리가 설치되어 있지 않아 군집 분석을 실행할 수 없습니다.\n\n"
                    "`pip install scikit-learn` 후 다시 실행해 주세요."
                )

            if sklearn_available:
                # 군집 분석은 "선택한 대분류 전체" 기준으로, 시도별 중분류 패턴을 사용
                if crime_main is not None and "범죄대분류" in df_reshaped.columns:
                    base_df = df_reshaped[df_reshaped["범죄대분류"] == crime_main].copy()
                else:
                    base_df = df_reshaped.copy()

                if "범죄중분류" not in base_df.columns:
                    st.info("군집 분석을 위한 '범죄중분류' 컬럼이 존재하지 않습니다.")
                else:
                    # 행: 범죄중분류, 열: 시도 → 전치하여 행: 시도, 열: 범죄중분류
                    heat_df = base_df[["범죄중분류"] + list(region_cols)].copy()
                    heat_df = heat_df.set_index("범죄중분류")

                    X = heat_df.T  # index: 지역, columns: 범죄중분류
                    X = X.fillna(0)

                    if X.shape[0] < 2:
                        st.info("군집 분석을 수행하기에 지역(시도) 수가 부족합니다.")
                    else:
                        st.markdown("#### 군집 분석 (K-means)")

                        # 클러스터 개수 선택 슬라이더
                        max_k = min(6, X.shape[0])  # 지역 수보다 많을 수 없음
                        n_clusters = st.slider(
                            "클러스터 개수 선택 (K)",
                            min_value=2,
                            max_value=max_k,
                            value=min(3, max_k),
                            step=1,
                        )

                        scaler = StandardScaler()
                        X_scaled = scaler.fit_transform(X)

                        kmeans = KMeans(
                            n_clusters=n_clusters,
                            random_state=42,
                            n_init=10,
                        )
                        labels = kmeans.fit_predict(X_scaled)

                        cluster_df = pd.DataFrame(
                            {
                                "지역": X.index,
                                "클러스터": labels,
                                "총발생건수": X.sum(axis=1).astype(int),
                            }
                        ).sort_values(["클러스터", "총발생건수"], ascending=[True, False])

                        # 클러스터별 색상용 문자열
                        cluster_df["클러스터명"] = cluster_df["클러스터"].apply(
                            lambda x: f"Cluster {x}"
                        )

                        # 클러스터별 막대그래프
                        fig_cluster = px.bar(
                            cluster_df,
                            x="총발생건수",
                            y="지역",
                            color="클러스터명",
                            orientation="h",
                            labels={"총발생건수": "총 발생 건수(건)", "지역": "시도"},
                            text="총발생건수",
                        )
                        fig_cluster.update_traces(texttemplate="%{text:,}건")
                        fig_cluster.update_layout(
                            margin=dict(l=10, r=10, t=10, b=10),
                            height=350,
                        )
                        st.plotly_chart(fig_cluster, use_container_width=True)

                        # 클러스터별 상세 테이블
                        st.markdown("#### 군집별 지역 목록")
                        st.dataframe(
                            cluster_df[["지역", "클러스터", "총발생건수"]]
                            .rename(
                                columns={
                                    "총발생건수": "총발생건수(건)",
                                }
                            )
                            .style.format({"총발생건수(건)": "{:,}"}),
                            use_container_width=True,
                            height=260,
                        )

                        # 간단한 해석 도움말
                        st.markdown(
                            """
                            - 같은 클러스터에 속한 시도들은 **유사한 범죄 패턴(중분류 구성)**을 가진 것으로 해석할 수 있습니다.
                            - 예를 들어, 특정 클러스터에 강력/폭력 관련 중분류 비중이 높다면, 해당 그룹을 별도로 관리·분석하는 근거로 활용할 수 있습니다.
                            """
                        )
        else:
            st.info("머신러닝 옵션 처리 중 알 수 없는 값이 선택되었습니다. 사이드바 설정을 다시 확인해 주세요.")
