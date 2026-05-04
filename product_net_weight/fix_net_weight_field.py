#!/usr/bin/env python3
"""
修复老数据库中净重字段定义的脚本
适用于解决"修改一个变体净重，其他变体也跟着变"的问题
"""

import logging

_logger = logging.getLogger(__name__)

def fix_net_weight_field(cr):
    """
    修复净重字段定义的函数
    """
    # 检查字段是否存在
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'product_product' AND column_name = 'net_weight'
    """)
    
    if not cr.fetchone():
        _logger.info("净重字段不存在，无需修复")
        return
    
    # 检查字段是否为计算字段（通过检查是否有对应的存储字段）
    cr.execute("""
        SELECT c.column_name, c.data_type, c.is_nullable
        FROM information_schema.columns c
        WHERE c.table_name = 'product_product' 
        AND c.column_name IN ('net_weight', 'id')
        ORDER BY c.column_name
    """)
    
    columns = {row[0]: row for row in cr.fetchall()}
    
    if 'net_weight' not in columns:
        _logger.info("净重字段不存在")
        return
    
    net_weight_info = columns['net_weight']
    
    # 如果字段定义正常（应该是浮点数字段），则无需修复
    if net_weight_info[1] == 'double precision' and net_weight_info[2] == 'YES':
        _logger.info("净重字段定义正常")
        return
    
    # 如果字段定义异常，需要重建
    _logger.info("检测到净重字段定义异常，开始修复...")
    
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
    
    _logger.info("净重字段修复完成")

def migrate(cr, version):
    """
    迁移函数，在模块升级时自动调用
    """
    if not version:
        return
    
    fix_net_weight_field(cr)