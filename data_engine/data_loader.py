# data_engine/data_loader.py

import pandas as pd
import streamlit as st
from config.mappings import VIP_MAPPING, get_age_group_by_birth_year

@st.cache_data(show_spinner=False)
def load_and_clean_data(coupon_file_path, sales_file_path):
    """
    读取两张CSV宽表，进行防弹级清洗与维度对齐。
    返回两张随时可用的 Clean DataFrames。
    """
    # 1. 读取原始数据
    df_coupon = pd.read_csv(coupon_file_path)
    df_sales = pd.read_csv(sales_file_path)

    # ==========================================
    # 2. 投入侧：优惠券数据清洗 (df_coupon)
    # ==========================================
    # 时间处理
    df_coupon['create_time'] = pd.to_datetime(df_coupon['create_time'])
    df_coupon['update_time'] = pd.to_datetime(df_coupon['update_time'])
    
    # 状态判定 (继承你原有的优秀逻辑)
    df_coupon['time_diff_hours'] = (df_coupon['update_time'] - df_coupon['create_time']).dt.total_seconds() / 3600
    def get_status_code(row):
        if row['coupon_status'] == 'available':
            return 3  # 闲置
        elif row['coupon_status'] == 'unavailable' and row['time_diff_hours'] > 23.5:
            return 2  # 系统过期
        else:
            return 1  # 真实核销
    df_coupon['status_code'] = df_coupon.apply(get_status_code, axis=1)

    # 维度对齐1：VIP等级升维 (新增统一列 'business_level')
    df_coupon['business_level'] = df_coupon['level'].map(VIP_MAPPING).fillna('平台会员')
    
    # 维度对齐2：保留优惠券原有的 'age_group' 字段，清理可能的空值
    df_coupon['age_group'] = df_coupon['age_group'].fillna('未知年龄')

    # ==========================================
    # 3. 产出侧：销售数据清洗 (df_sales)
    # ==========================================
    # 金额与时间处理
    df_sales['销售额'] = pd.to_numeric(df_sales['销售额'], errors='coerce').fillna(0)
    df_sales['销售时间'] = pd.to_datetime(df_sales['销售时间'])
    
    # 维度对齐1：统一 VIP 列名 (将销售表的'会员等级'直接赋给'business_level')
    df_sales['business_level'] = df_sales['会员等级'].fillna('平台会员')
    
    # 维度对齐2：统一年龄列 (将销售表的'生日'转换为'age_group')
    # 即使销售表只有具体的'年龄'，或者'生日'，这里统一降维为'XX后'
    if '生日' in df_sales.columns:
        df_sales['age_group'] = df_sales['生日'].apply(get_age_group_by_birth_year)
    else:
        # 万一数据里没有生日只有年龄的备用逻辑
        df_sales['age_group'] = '未知年龄' 

    return df_coupon, df_sales