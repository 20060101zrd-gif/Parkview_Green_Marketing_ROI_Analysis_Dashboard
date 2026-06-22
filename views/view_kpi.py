import streamlit as st
import pandas as pd

def render_kpi_overview(df_coupon, df_sales):
    """
    渲染首屏核心 KPI 对标区
    """
    # ==========================================
    # 1. 核心指标计算
    # ==========================================
    # 投入侧计算
    total_issued = len(df_coupon)
    real_used = len(df_coupon[df_coupon['status_code'] == 1])
    conversion_rate = (real_used / total_issued * 100) if total_issued > 0 else 0
    
    # 产出侧计算
    total_sales = df_sales['销售额'].sum()
    total_orders = len(df_sales)
    aov = total_sales / total_orders if total_orders > 0 else 0
    
    # 会员贡献计算 (剔除平台会员/非会员)
    member_sales = df_sales[df_sales['business_level'] != '平台会员']['销售额'].sum()
    member_contribution = (member_sales / total_sales * 100) if total_sales > 0 else 0
    
    # 营销杠杆率估算: 核销的券数 * 整体客单价 (这代表如果没有这些券，可能会流失的业绩)
    estimated_coupon_sales = real_used * aov
    coupon_leverage = (estimated_coupon_sales / total_sales * 100) if total_sales > 0 else 0

    # ==========================================
    # 2. UI 渲染呈现
    # ==========================================
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.info(" **投入侧：发券效能**")
        st.metric("总发券量 (张)", f"{total_issued:,}")
        st.metric("真实核销转化率", f"{conversion_rate:.2f}%")

    with col2:
        st.success(" **产出侧：整体业绩**")
        st.metric("总销售额 (¥)", f"{total_sales:,.0f}")
        st.metric("整体客单价 (¥)", f"{aov:,.0f}")

    with col3:
        st.warning(" **会员价值贡献**")
        st.metric("会员消费总额 (¥)", f"{member_sales:,.0f}")
        st.metric("会员业绩大盘占比", f"{member_contribution:.1f}%")

    with col4:
        st.error(" **营销杠杆率 (估算)**")
        st.metric("券核销带动销售额 (¥)", f"{estimated_coupon_sales:,.0f}")
        st.metric("发券动销渗透率", f"{coupon_leverage:.1f}%", help="估算逻辑：核销数 × 当期整体客单价 / 总销售额")