import streamlit as st
import pandas as pd

def render_cohort_analysis(df_coupon, df_sales):
    """
    渲染战役三 & 六：人群分层与群体对标表 (严谨商务优化版)
    """
    st.markdown("---")
    st.subheader("高价值客群分层与投入产出对标")
    
    # 优化后的业务价值文案
    st.markdown("**业务价值**：跨系统定位「高营销敏感度+高客单回报」的核心利润客群，精准识别「高券资源占用+低价值贡献」的低效耗损客群，支撑营销资源精准投放与客群精细化运营。")
    st.caption("注：本对标模型为群体维度聚合统计，旨在评估整体人群的营销投入产出效率与资产健康度。")

    # ===== 新增：客群分层判定规则说明表 =====
    st.markdown("""
    | 标签 | 客群类型 | 核心判定规则 | 运营建议 |
    | :--- | :--- | :--- | :--- |
    | 🔴 | 券效耗损型客群 | 人均领券≥5张 且 客单价＜200元 | 熔断止损，缩减营销投入 |
    | 🟡 | 自然高价值客群 | 客单价≥1000元 且 券核销率＜2% | 重点维护，侧重留存与服务 |
    | 🟢 | 高ROI转化客群 | 券核销率≥1% 且 客单价≥500元 | 加大倾斜，放大营销杠杆 |
    | ⚪ | 常规基石客群 | 无显著特征的基础人群 | 常态化运营，稳步提升 |
    """)
    st.markdown("---")

    if df_coupon.empty and df_sales.empty:
        st.warning("当前无数据可供分层分析。")
        return

    # ==========================================
    # 1. 投入侧 (优惠券) 人群聚合
    # ==========================================
    if not df_coupon.empty:
        df_c_agg = df_coupon.groupby(['business_level', 'age_group']).agg(
            总领券量=('coupon_record_id', 'count'),
            核销数=('status_code', lambda x: (x==1).sum()),
            发券人数=('userid', 'nunique')
        ).reset_index()
        df_c_agg['人均领券数'] = (df_c_agg['总领券量'] / df_c_agg['发券人数']).round(1)
        df_c_agg['券核销率'] = (df_c_agg['核销数'] / df_c_agg['总领券量'].replace(0, 1))
    else:
        df_c_agg = pd.DataFrame(columns=['business_level', 'age_group', '发券人数', '人均领券数', '券核销率'])

    # ==========================================
    # 2. 产出侧 (销售) 人群聚合
    # ==========================================
    if not df_sales.empty:
        df_s_agg = df_sales.groupby(['business_level', 'age_group']).agg(
            总销售额=('销售额', 'sum'),
            订单数=('科创编号', 'count'), 
            消费人数=('电话', 'nunique') 
        ).reset_index()
        df_s_agg['消费频次'] = (df_s_agg['订单数'] / df_s_agg['消费人数'].replace(0, 1)).round(1)
        df_s_agg['客单价'] = (df_s_agg['总销售额'] / df_s_agg['订单数'].replace(0, 1)).round(0)
    else:
        df_s_agg = pd.DataFrame(columns=['business_level', 'age_group', '消费人数', '消费频次', '客单价', '总销售额'])

    # ==========================================
    # 3. 双端数据合并对标 (Cohort Merge)
    # ==========================================
    cohort_df = pd.merge(df_c_agg, df_s_agg, on=['business_level', 'age_group'], how='outer').fillna(0)
    cohort_df = cohort_df[(cohort_df.get('总领券量', 0) > 0) | (cohort_df.get('总销售额', 0) > 0)]

    # ==========================================
    # 4. 机器自动打标签诊断 (优化命名与注释)
    # ==========================================
    def generate_tags(row):
        avg_coupon = float(row.get('人均领券数', 0.0))
        usage_rate = float(row.get('券核销率', 0.0))
        atv = float(row.get('客单价', 0.0))
            
        # 🔴 规则1：券效耗损型客群 -> 高券资源占用，低客单产出，建议熔断止损
        if avg_coupon >= 5.0 and atv < 200.0:
            return '🔴 券效耗损型客群'
            
        # 🟡 规则2：自然高价值客群 -> 高客单贡献，几乎不依赖优惠券杠杆
        elif atv >= 1000.0 and usage_rate < 0.02:
            return '🟡 自然高价值客群'
            
        # 🟢 规则3：高ROI转化客群 -> 营销敏感度高，客单转化回报优异
        elif usage_rate >= 0.01 and atv >= 500.0:
            return '🟢 高ROI转化客群'
            
        else:
            return '⚪ 常规基石客群'

    cohort_df['群体诊断结论'] = cohort_df.apply(generate_tags, axis=1)

    # ==========================================
    # 5. UI 渲染呈现 (高级热力图 + 干净索引版)
    # ==========================================
    display_cols = [
        'business_level', 'age_group', 
        '发券人数', '人均领券数', '券核销率', 
        '消费人数', '消费频次', '客单价', '总销售额', 
        '群体诊断结论'
    ]
    display_cols = [c for c in display_cols if c in cohort_df.columns]
    
    # 通过 .reset_index(drop=True) 抹平脏行号，生成整齐序号
    display_df = cohort_df[display_cols].sort_values(by='总销售额', ascending=False).reset_index(drop=True)
    display_df = display_df.rename(columns={'business_level': '会员等级', 'age_group': '世代人群'})

    # 渲染带有专业质感的热力色背景表
    try:
        styled_df = display_df.style.format({
            '客单价': '¥{:.0f}',
            '总销售额': '¥{:.0f}',
            '发券人数': '{:.0f}',
            '消费人数': '{:.0f}',
            '人均领券数': '{:.1f}',
            '消费频次': '{:.1f}',
            '券核销率': '{:.1%}'
        }).background_gradient(subset=['总销售额'], cmap='Reds') \
          .background_gradient(subset=['人均领券数'], cmap='Blues')
          
        st.dataframe(styled_df, use_container_width=True, height=430)
    except Exception as e:
        # 降级兜底方案
        st.dataframe(display_df, use_container_width=True, height=430)