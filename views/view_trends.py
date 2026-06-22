import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def render_trends_chart(df_coupon, df_sales):
    """
    营销节奏与业绩滞后性对标 - 最终精简版
    主界面：核心双轴趋势图 + 指标卡片 + 智能结论
    折叠区：底层数据、相关性全量结果、散点图
    """
    st.markdown("---")
    st.subheader("营销节奏与业绩滞后性对标")
    
    # 业务价值说明
    st.markdown("**业务价值**：通过营销投入与终端销售的联动对比，观测营销投入的业绩转化周期与滞后效应，验证营销投入有效性，辅助营销排期与预算分配决策。")

    if len(df_coupon) == 0 or len(df_sales) == 0:
        st.warning("当前筛选条件下数据量不足，无法生成趋势图。")
        return

    # ==========================================
    # 交互控件区（4个核心控件）
    # ==========================================
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        time_granularity = st.selectbox(
            "时间粒度",
            options=["月度", "周度"],
            index=0,
            help="周度粒度可观测更精细的核销转化周期，月度适合看长期趋势"
        )
    
    with col2:
        analysis_metric = st.selectbox(
            "分析指标",
            options=["发券量", "核销量"],
            index=0,
            help="核销量更能真实反映营销对业绩的拉动作用"
        )
    
    # 根据时间粒度动态切换滞后期选项
    with col3:
        if time_granularity == "月度":
            lag_options = [0, 1, 2, 3, 6]
            lag_unit = "个月"
        else:
            lag_options = [0, 1, 2, 4, 8]
            lag_unit = "周"
            
        lag_period = st.selectbox(
            f"滞后周期（{lag_unit}）",
            options=lag_options,
            index=0,
            help="将营销指标向后平移对应周期，对比与销售额的匹配度"
        )
    
    with col4:
        # 客群范围筛选
        all_levels = ["全部客群"] + sorted(df_coupon["business_level"].unique().tolist())
        selected_level = st.selectbox(
            "会员等级筛选",
            options=all_levels,
            index=0,
            help="可单独筛选高敏感/高价值客群，验证精准客群的滞后效应"
        )

    # ==========================================
    # 1. 数据预处理（周度ISO标准排序，修复跨年排序bug）
    # ==========================================
    df_c = df_coupon.copy()
    df_s = df_sales.copy()
    
    # 按选中的会员等级过滤数据
    if selected_level != "全部客群":
        df_c = df_c[df_c["business_level"] == selected_level]
        df_s = df_s[df_s["business_level"] == selected_level]
    
    # 时间粒度转换 + 排序键
    if time_granularity == "月度":
        df_c['time_period'] = df_c['create_time'].dt.strftime('%Y-%m')
        df_s['time_period'] = df_s['销售时间'].dt.strftime('%Y-%m')
        df_c['sort_key'] = df_c['create_time'].dt.to_period('M').dt.to_timestamp()
        df_s['sort_key'] = df_s['销售时间'].dt.to_period('M').dt.to_timestamp()
    else:
        # 周度：ISO标准周，彻底解决跨年周排序错乱
        df_c['iso_year'] = df_c['create_time'].dt.isocalendar().year
        df_c['iso_week'] = df_c['create_time'].dt.isocalendar().week
        df_c['time_period'] = df_c['iso_year'].astype(str) + "-W" + df_c['iso_week'].astype(str).str.zfill(2)
        df_c['sort_key'] = df_c['create_time'] - pd.to_timedelta(df_c['create_time'].dt.weekday, unit='D')
        
        df_s['iso_year'] = df_s['销售时间'].dt.isocalendar().year
        df_s['iso_week'] = df_s['销售时间'].dt.isocalendar().week
        df_s['time_period'] = df_s['iso_year'].astype(str) + "-W" + df_s['iso_week'].astype(str).str.zfill(2)
        df_s['sort_key'] = df_s['销售时间'] - pd.to_timedelta(df_s['销售时间'].dt.weekday, unit='D')

    # 聚合营销侧数据
    trend_coupon = df_c.groupby(['time_period', 'sort_key']).agg(
        issued_count=('coupon_record_id', 'count'),
        redeemed_count=('status_code', lambda x: (x == 1).sum())
    ).reset_index()
    
    # 聚合销售侧数据
    trend_sales = df_s.groupby(['time_period', 'sort_key'])['销售额'].sum().reset_index(name='sales_amount')

    # 合并数据，按时间排序
    df_trend = pd.merge(trend_coupon, trend_sales, on=['time_period', 'sort_key'], how='outer').fillna(0)
    df_trend = df_trend.sort_values('sort_key').reset_index(drop=True)
    
    # 选择当前分析的指标列
    metric_col = 'issued_count' if analysis_metric == "发券量" else 'redeemed_count'
    metric_name = f"{analysis_metric}（滞后{lag_period}{lag_unit}）"

    # ==========================================
    # 自动计算所有滞后期相关性，识别最优转化周期
    # ==========================================
    def calc_lag_corr(lag):
        """计算指定滞后期的相关性系数，自动忽略空值"""
        lagged = df_trend[metric_col].shift(lag)
        valid = pd.DataFrame({'lagged': lagged, 'sales': df_trend['sales_amount']}).dropna()
        if len(valid) < 3:
            return 0
        return valid['lagged'].corr(valid['sales'])
    
    lag_corr_results = {lag: calc_lag_corr(lag) for lag in lag_options}
    best_lag = max(lag_corr_results, key=lag_corr_results.get)
    best_corr = lag_corr_results[best_lag]

    # ==========================================
    # 2. 核心指标统计卡片
    # ==========================================
    df_trend['metric_lagged'] = df_trend[metric_col].shift(lag_period)
    valid_data = df_trend[['metric_lagged', 'sales_amount']].dropna()
    current_corr = valid_data['metric_lagged'].corr(valid_data['sales_amount']) if len(valid_data) >= 3 else 0

    total_issued = int(df_trend['issued_count'].sum())
    total_redeemed = int(df_trend['redeemed_count'].sum())
    total_sales = df_trend['sales_amount'].sum()
    redeem_rate = (total_redeemed / total_issued * 100) if total_issued > 0 else 0

    card_col1, card_col2, card_col3, card_col4 = st.columns(4)
    with card_col1:
        st.metric(f"累计{analysis_metric}", f"{int(df_trend[metric_col].sum())} 张")
    with card_col2:
        st.metric("累计销售额", f"¥{total_sales:,.0f}")
    with card_col3:
        st.metric("累计核销率", f"{redeem_rate:.1f}%")
    with card_col4:
        st.metric(
            "当前相关性系数", 
            f"{current_corr:.2f}",
            delta=f"最优: 滞后{best_lag}{lag_unit} ({best_corr:.2f})",
            delta_color="off"
        )

    # 智能业务结论
    if abs(current_corr) >= 0.7:
        st.success(f"📊 数据结论：滞后{lag_period}{lag_unit}时，{analysis_metric}与销售额呈**强正相关**，营销转化周期高度匹配该滞后期。")
    elif 0.4 <= abs(current_corr) < 0.7:
        st.info(f"📊 数据结论：滞后{lag_period}{lag_unit}时，{analysis_metric}与销售额呈**中等正相关**，营销有一定滞后拉动作用。")
    else:
        st.warning(f"📊 数据结论：滞后{lag_period}{lag_unit}时，{analysis_metric}与销售额**相关性较弱**，业绩波动受其他因素影响更大。")

    # ==========================================
    # 3. 主界面：双轴趋势图（核心可视化）
    # ==========================================
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 仅标注销售额Top30%的峰值，避免标签拥挤
    sales_threshold = df_trend['sales_amount'].quantile(0.7)
    sales_text = df_trend['sales_amount'].apply(
        lambda x: f"¥{x:,.0f}" if x >= sales_threshold and x > 0 else ""
    )
    
    # 柱状图：滞后后的营销指标
    fig.add_trace(
        go.Bar(
            x=df_trend['time_period'], 
            y=df_trend['metric_lagged'], 
            name=metric_name, 
            marker_color='#3498db', 
            opacity=0.8,
            text=df_trend['metric_lagged'].apply(lambda x: int(x) if pd.notna(x) and x > 0 else ""),
            textposition='outside',
            textfont=dict(color='#ffffff')
        ),
        secondary_y=False,
    )

    # 折线图：销售额
    fig.add_trace(
        go.Scatter(
            x=df_trend['time_period'], 
            y=df_trend['sales_amount'], 
            name="销售额 (¥)", 
            mode='lines+markers+text',
            text=sales_text,
            textposition="top center",
            textfont=dict(color='#ffffff'),
            line=dict(color='#e74c3c', width=3), 
            marker=dict(size=7, color='#e74c3c')
        ),
        secondary_y=True,
    )

    # 布局与样式
    fig.update_layout(
        title_text=f"<b>{time_granularity}{analysis_metric}投入 vs 销售产出对比</b>",
        title_font=dict(color='#ffffff', size=16),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified",
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1,
            font=dict(color='#ffffff')
        ),
        margin=dict(l=20, r=20, t=60, b=20),
        font=dict(color='#e0e0e0')
    )
    
    # Y轴配置
    fig.update_yaxes(
        title_text=f"{analysis_metric}数量 (张)", 
        secondary_y=False, 
        showgrid=False, 
        rangemode='tozero',
        title_font=dict(color='#e0e0e0'),
        tickfont=dict(color='#e0e0e0')
    )
    fig.update_yaxes(
        title_text="销售额 (元)", 
        secondary_y=True, 
        showgrid=True, 
        gridcolor='rgba(255,255,255,0.1)',
        rangemode='tozero',
        title_font=dict(color='#e0e0e0'),
        tickfont=dict(color='#e0e0e0')
    )
    
    # X轴配置
    fig.update_xaxes(
        tickangle=-45,
        tickfont=dict(size=10, color='#e0e0e0'),
        showgrid=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # 底部折叠面板：开发者调试（散点图移至此处）
    # ==========================================
    with st.expander("🔧 开发者调试：查看底层数据与计算明细"):
        tab1, tab2, tab3 = st.tabs(["聚合明细数据", "滞后期相关性全量", "相关性散点图"])
        
        # Tab1：底层明细数据
        with tab1:
            st.markdown(f"**有效样本量**：{len(df_trend)}个{time_granularity}周期")
            st.dataframe(
                df_trend[['time_period', metric_col, 'metric_lagged', 'sales_amount']], 
                use_container_width=True,
                hide_index=True
            )
        
        # Tab2：全滞后期相关性结果
        with tab2:
            corr_df = pd.DataFrame({
                f"滞后周期（{lag_unit}）": lag_options,
                "相关性系数": [round(lag_corr_results[lag], 4) for lag in lag_options]
            })
            st.dataframe(corr_df, use_container_width=True, hide_index=True)

        # Tab3：散点图（原主界面内容移至此）
        with tab3:
            col_scatter_left, col_scatter_right = st.columns([3, 1])
            
            with col_scatter_left:
                fig_scatter = go.Figure()
                
                # 散点数据
                fig_scatter.add_trace(go.Scatter(
                    x=valid_data['metric_lagged'],
                    y=valid_data['sales_amount'],
                    mode='markers',
                    name='数据点',
                    marker=dict(color='#3498db', size=8, opacity=0.7),
                    hovertemplate=f'{analysis_metric}: %{{x}}张<br>销售额: ¥%{{y:,.0f}}<extra></extra>'
                ))
                
                # 线性拟合线
                if len(valid_data) >= 3:
                    z = np.polyfit(valid_data['metric_lagged'], valid_data['sales_amount'], 1)
                    p = np.poly1d(z)
                    x_line = np.linspace(valid_data['metric_lagged'].min(), valid_data['metric_lagged'].max(), 100)
                    
                    fig_scatter.add_trace(go.Scatter(
                        x=x_line,
                        y=p(x_line),
                        mode='lines',
                        name=f'拟合线 (R={current_corr:.2f})',
                        line=dict(color='#e74c3c', width=2, dash='dash')
                    ))
                
                # 样式适配
                fig_scatter.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis_title=f"{analysis_metric}（滞后{lag_period}{lag_unit}，张）",
                    yaxis_title="销售额（元）",
                    font=dict(color='#e0e0e0'),
                    margin=dict(l=20, r=20, t=20, b=20),
                    legend=dict(font=dict(color='#ffffff'))
                )
                fig_scatter.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                fig_scatter.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                
                st.plotly_chart(fig_scatter, use_container_width=True)
            
            with col_scatter_right:
                st.metric("相关系数 R", f"{current_corr:.2f}")
                st.caption("R越接近1，正向线性关系越强；越接近0，线性关系越弱。")
                st.divider()
                st.metric("最优滞后期", f"滞后{best_lag}{lag_unit}")
                st.metric("最优相关系数", f"{best_corr:.2f}")