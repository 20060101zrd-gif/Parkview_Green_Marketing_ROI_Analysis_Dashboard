# components/filters.py
import streamlit as st
import pandas as pd

def render_global_filters(df_coupon, df_sales):
    """
    在侧边栏渲染全局筛选器，并同时过滤投入表(Coupon)和产出表(Sales)
    """
    # ==========================================
    # 注入自定义 CSS：将选中标签改为透明底+边框的高级样式
    # ==========================================
    st.markdown(
        """
        <style>
        /* 针对多选框选中的标签 (Tag) */
        span[data-baseweb="tag"] {
            background-color: transparent !important; /* 背景完全透明 */
            border: 1px solid #8892B0 !important;     /* 极简的高级灰蓝边框 */
        }
        
        /* 标签内部的文字颜色 */
        span[data-baseweb="tag"] span[title] {
            color: #E2E8F0 !important; 
        }
        
        /* 标签右侧的 'x' 关闭按钮背景透明化 */
        span[data-baseweb="tag"] span[role="presentation"] {
            background-color: transparent !important;
            color: #8892B0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.markdown("---")
    st.sidebar.title("2. 全局交叉分析控制台")
    st.sidebar.markdown("*(以下筛选将同步对齐投入与产出数据)*")

    # 1. 时间范围筛选 (以优惠券发放时间为锚点)
    min_date = df_coupon['create_time'].dt.date.min()
    max_date = df_coupon['create_time'].dt.date.max()
    
    selected_date = st.sidebar.date_input(
        "数据时间范围",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # 防止用户只选了一个开始日期还没选结束日期
    if len(selected_date) == 2:
        start_date, end_date = selected_date
    else:
        start_date, end_date = selected_date[0], selected_date[0]

    # ==========================================
    # 专业化高级折叠面板 (Popover 悬浮窗)
    # ==========================================
    with st.sidebar.popover("展开客群精细化筛选面板", use_container_width=True):
        st.markdown("**请勾选需要聚焦的特定客群维度：**\n*(默认留空即代表查看全量大盘)*")

        # 2. 世代维度筛选 (强制业务逻辑排序)
        ordered_ages = ['70前', '70后', '80后', '90后', '00后', '未知年龄']
        # 确保只展示数据中存在的选项
        all_ages = [age for age in ordered_ages if age in df_coupon['age_group'].unique()]
        
        selected_age = st.multiselect(
            "客群世代圈层 (Age Cohort)", 
            options=all_ages, 
            default=[],  # 核心：默认留空，避免满屏红砖块
            placeholder="包含全量世代 (点击下拉聚焦)..."
        )

        # 3. 会员等级筛选 (强制业务逻辑排序)
        all_levels = ['平台会员', '绿意会员', '悦意会员', '菁英会员']
        selected_level = st.multiselect(
            "会员资产分层 (Membership Tier)", 
            options=all_levels, 
            default=[],  # 核心：默认留空
            placeholder="包含全量等级 (点击下拉聚焦)..."
        )

    # ==========================================
    # 执行过滤逻辑 (留空即全选的底层判断)
    # ==========================================
    
    # 如果列表为空（用户没选），则自动赋值为全量列表，保证数据不丢失
    final_age_filter = selected_age if selected_age else all_ages
    final_level_filter = selected_level if selected_level else all_levels
    
    # 过滤优惠券表
    mask_coupon = (
        (df_coupon['create_time'].dt.date >= start_date) &
        (df_coupon['create_time'].dt.date <= end_date) &
        (df_coupon['age_group'].isin(final_age_filter)) &
        (df_coupon['business_level'].isin(final_level_filter))
    )
    df_coupon_filtered = df_coupon[mask_coupon]

    # 过滤销售表
    mask_sales = (
        (df_sales['销售时间'].dt.date >= start_date) &
        (df_sales['销售时间'].dt.date <= end_date) &
        (df_sales['age_group'].isin(final_age_filter)) &
        (df_sales['business_level'].isin(final_level_filter))
    )
    df_sales_filtered = df_sales[mask_sales]

    return df_coupon_filtered, df_sales_filtered