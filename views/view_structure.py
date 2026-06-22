import streamlit as st
import pandas as pd
import plotly.express as px

def render_structure_analysis(df_coupon, df_sales):
    """
    渲染结构拆解对比区 (券种结构 vs 业态业绩结构)
    """
    st.markdown("---")
    st.subheader("投入资源与产出业绩的结构拆解")
    
    # 左右分栏对照
    col1, col2 = st.columns(2)

    # ==========================================
    # 1. 投入侧：优惠券种结构 (环形图)
    # ==========================================
    with col1:
        st.markdown("#### 钱花哪了？(各券种发行量占比)")
        if not df_coupon.empty:
            df_coupon_agg = df_coupon['coupon_type'].value_counts().reset_index()
            df_coupon_agg.columns = ['券种类型', '发券数量']
            
            # 【优化3】券种名称中英映射，自动转换为业务中文名
            coupon_name_map = {
                'daily_parking_coupon': '日常停车券',
                'user_exchange': '用户兑换券',
                'activity_coupon': '活动券',
                'parking_coupon': '停车券',
                'voucher': '代金券',
                'cash_coupon': '现金券',
                'discount_coupon': '折扣券'
            }
            # 匹配映射，未匹配到的保留原名
            df_coupon_agg['券种类型'] = df_coupon_agg['券种类型'].map(coupon_name_map).fillna(df_coupon_agg['券种类型'])

            # 【优化4】自动输出结构洞察，点出核心投放特征
            total_coupon = df_coupon_agg['发券数量'].sum()
            top_coupon = df_coupon_agg.iloc[0]
            top_ratio = top_coupon['发券数量'] / total_coupon
            st.caption(f"💡 营销投入高度集中于{top_coupon['券种类型']}，其余券种投放占比仅{1-top_ratio:.1%}")
            
            fig_coupon = px.pie(
                df_coupon_agg, 
                values='发券数量', 
                names='券种类型', 
                hole=0.45,  # 设置为环形图
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_coupon.update_traces(textposition='inside', textinfo='percent+label')
            fig_coupon.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False # 隐藏图例，让环形图更大更清晰
            )
            st.plotly_chart(fig_coupon, use_container_width=True)
        else:
            st.info("无满足当前筛选条件的优惠券数据")

    # ==========================================
    # 2. 产出侧：销售业态结构 (条形图)
    # ==========================================
    with col2:
        st.markdown("#### 业绩从哪来？(核心业态销售额排名)")
        if not df_sales.empty:
            # 按业态聚合销售额
            df_sales_agg = df_sales.groupby('业态')['销售额'].sum().reset_index()
            # 排序：条形图从大到小排列需要由底向上升序
            df_sales_agg = df_sales_agg.sort_values('销售额', ascending=True)
            
            fig_sales = px.bar(
                df_sales_agg, 
                x='销售额', 
                y='业态', 
                orientation='h', # 水平条形图
                text_auto='.2s', # 自动在柱子上显示简化的金额 (如 1.2M)
                color='销售额', 
                color_continuous_scale='Reds' # 业绩越高颜色越深
            )
            fig_sales.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                xaxis_title="销售总额 (元)",
                yaxis_title="",
                coloraxis_showscale=False # 隐藏右侧颜色条
            )
            st.plotly_chart(fig_sales, use_container_width=True)
        else:
            st.info("无满足当前筛选条件的销售数据")