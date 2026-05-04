#!/usr/bin/env python3
"""
净重字段修复迁移脚本 - 预迁移检查
"""

def pre_migrate(cr, version):
    """
    预迁移检查：诊断老数据库中的字段问题
    """
    # 检查净重字段定义
    cr.execute("""
        SELECT 
            column_name, 
            data_type, 
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_name = 'product_product' AND column_name = 'net_weight'
    """)
    
    field_info = cr.fetchone()
    
    if field_info:
        print(f"净重字段信息: {field_info}")
        
        # 检查是否有异常的定义
        if field_info[3]:  # column_default 不为空，可能是计算字段
            print("警告：净重字段可能有计算字段定义，需要修复")
        
        if field_info[1] != 'double precision':  # 数据类型异常
            print("警告：净重字段数据类型异常，需要修复")
    else:
        print("净重字段不存在，将正常创建")