#!/usr/bin/env python3
"""
净重字段修复迁移脚本 - 迁移后修复
"""

def migrate(cr, version):
    """
    迁移后修复：确保净重字段定义正确
    """
    # 检查并修复净重字段
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'product_product' AND column_name = 'net_weight'
    """)
    
    if not cr.fetchone():
        print("净重字段不存在，创建新字段")
        cr.execute("""
            ALTER TABLE product_product 
            ADD COLUMN net_weight double precision
        """)
        return
    
    # 检查字段定义是否正常
    cr.execute("""
        SELECT data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'product_product' AND column_name = 'net_weight'
    """)
    
    data_type, is_nullable, column_default = cr.fetchone()
    
    # 如果字段定义异常，重建字段
    needs_fix = False
    
    if data_type != 'double precision':
        print(f"数据类型异常: {data_type}，需要修复")
        needs_fix = True
    
    if is_nullable != 'YES':
        print("字段不可为空，需要修复")
        needs_fix = True
        
    if column_default:
        print(f"字段有默认值: {column_default}，可能是计算字段，需要修复")
        needs_fix = True
    
    if needs_fix:
        print("开始修复净重字段...")
        
        # 备份数据
        cr.execute("""
            CREATE TABLE IF NOT EXISTS product_product_net_weight_backup AS
            SELECT id, net_weight FROM product_product WHERE net_weight IS NOT NULL
        """)
        
        # 删除异常字段
        cr.execute("ALTER TABLE product_product DROP COLUMN IF EXISTS net_weight")
        
        # 重新创建正确的字段
        cr.execute("""
            ALTER TABLE product_product 
            ADD COLUMN net_weight double precision
        """)
        
        # 恢复数据
        cr.execute("""
            UPDATE product_product pp
            SET net_weight = backup.net_weight
            FROM product_product_net_weight_backup backup
            WHERE pp.id = backup.id
        """)
        
        # 清理备份表
        cr.execute("DROP TABLE IF EXISTS product_product_net_weight_backup")
        
        print("净重字段修复完成")
    else:
        print("净重字段定义正常，无需修复")