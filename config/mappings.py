# config/mappings.py

# 1. 优惠券VIP底层代码 -> 业务统一名称映射
VIP_MAPPING = {
    '非会员': '平台会员',
    'VIP 1002': '绿意会员',   # 假设1002对应绿意，如果有误你后续可直接在此修改
    'VIP 1003': '悦意会员',
    'VIP 1004': '菁英会员'
}

# 2. 根据出生年份计算所属世代的函数（处理销售表）
def get_age_group_by_birth_year(birth_date_str):
    """
    输入: '1988-07-21' (来自销售表)
    输出: '80后', '90后' 等，与优惠券表对齐
    """
    try:
        # 提取年份前四位
        year = int(str(birth_date_str)[:4])
        if year >= 2000:
            return '00后'
        elif 1990 <= year <= 1999:
            return '90后'
        elif 1980 <= year <= 1989:
            return '80后'
        elif 1970 <= year <= 1979:
            return '70后'
        else:
            return '60后及以前'
    except:
        return '未知年龄'