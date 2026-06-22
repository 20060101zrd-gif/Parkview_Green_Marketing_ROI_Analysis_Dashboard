# app.py
import streamlit as st
from views.view_kpi import render_kpi_overview
from views.view_trends import render_trends_chart
from views.view_cohorts import render_cohort_analysis
from views.view_structure import render_structure_analysis
# 导入我们的自定义模块
from data_engine.data_loader import load_and_clean_data
from components.filters import render_global_filters

# ==========================================
# 0. 页面全局设置 (必须在第一行)
# ==========================================
st.set_page_config(page_title="北京侨福芳草地 | 营销效能与客群价值分析", layout="wide")

# ==========================================
# 1. 数据上传区 (对应你的方式二)
# ==========================================
st.sidebar.title(" 1. 载入双端数据源")
coupon_file = st.sidebar.file_uploader(" 上传投入侧 ", type=['csv'])
sales_file = st.sidebar.file_uploader(" 上传产出侧 ", type=['csv'])

# ==========================================
# 2. 核心路由与页面加载
# ==========================================
if coupon_file is not None and sales_file is not None:
    with st.spinner(' 数据引擎运转中：正在进行双表维度对齐与清洗...'):
        # 1. 呼叫数据引擎洗菜
        df_coupon_clean, df_sales_clean = load_and_clean_data(coupon_file, sales_file)
    
    st.sidebar.success("✅ 底层数据融合完毕")
    
    # 2. 呼叫全局筛选器，获取用户点单后的最新数据
    df_coupon_filtered, df_sales_filtered = render_global_filters(df_coupon_clean, df_sales_clean)

    # 3. 渲染主页面架构
    st.title(" 北京侨福芳草地 | 营销效能与客群价值分析 ")
    st.markdown("打通发券 - 核销 - 消费全链路，识别高 ROI 转化客群与低效营销投入，支撑精准营销与资源优化配置。")
    st.markdown("---")
    
    # 确保有过滤后的数据才显示视图
    if len(df_coupon_filtered) > 0 and len(df_sales_filtered) > 0:
        # 【优化1】移除开发向提示，仅保留业务向的数据范围说明
        st.write(f"当前选定范围包含：**{len(df_coupon_filtered):,}** 条发券记录，**{len(df_sales_filtered):,}** 条销售记录。")

        
        
        # 渲染业务模块
        render_kpi_overview(df_coupon_filtered, df_sales_filtered)
        render_structure_analysis(df_coupon_filtered, df_sales_filtered)
        render_trends_chart(df_coupon_filtered, df_sales_filtered)
        render_cohort_analysis(df_coupon_filtered, df_sales_filtered)

    else:
        st.warning("⚠️ 当前筛选条件下无数据，请放宽左侧的筛选范围。")

else:
    # 欢迎页空白状态
    st.info("👈 请在左侧面板依次上传两份 CSV 数据以启动战情室。")