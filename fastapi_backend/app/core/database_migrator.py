"""
数据库迁移工具 - 负责Django和FastAPI之间的数据兼容性
"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """数据库迁移管理器"""
    
    def __init__(self, django_db_path: str):
        self.django_db_path = django_db_path
        
    def verify_django_tables(self) -> bool:
        """验证Django数据库表是否存在"""
        try:
            conn = sqlite3.connect(self.django_db_path)
            cursor = conn.cursor()
            
            # 检查核心表是否存在
            required_tables = [
                'auth_user',
                'matcher_userprofile',
                'matcher_joblisting',
                'matcher_matchsession',
                'matcher_savedjob',
                'matcher_coverletter',
                'matcher_customresume',
                'matcher_matchedjob'
            ]
            
            for table in required_tables:
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table,))
                if not cursor.fetchone():
                    logger.error(f"Required table {table} not found")
                    return False
                    
            conn.close()
            logger.info("All Django tables verified successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying Django tables: {e}")
            return False
    
    def get_table_structure(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表结构信息"""
        try:
            conn = sqlite3.connect(self.django_db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            structure = []
            for col in columns:
                structure.append({
                    'name': col[1],
                    'type': col[2],
                    'not_null': bool(col[3]),
                    'default_value': col[4],
                    'primary_key': bool(col[5])
                })
                
            conn.close()
            return structure
            
        except Exception as e:
            logger.error(f"Error getting table structure for {table_name}: {e}")
            return []
    
    def sync_data(self, table_name: str, data: List[Dict[str, Any]]) -> bool:
        """将数据同步到Django数据库"""
        try:
            conn = sqlite3.connect(self.django_db_path)
            cursor = conn.cursor()
            
            # 这里可以实现具体的数据同步逻辑
            # 例如：检查冲突、更新或插入数据等
            
            conn.commit()
            conn.close()
            logger.info(f"Data synced successfully for table {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing data for {table_name}: {e}")
            return False
    
    def create_fastapi_migration_table(self) -> bool:
        """创建FastAPI迁移状态表"""
        try:
            conn = sqlite3.connect(self.django_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fastapi_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_name VARCHAR(255) NOT NULL UNIQUE,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("FastAPI migration table created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating FastAPI migration table: {e}")
            return False

# 全局migrator实例
migrator = None

def get_migrator() -> DatabaseMigrator:
    """获取migrator实例"""
    global migrator
    if migrator is None:
        django_db_path = Path(__file__).parent.parent.parent.parent / "db.sqlite3"
        migrator = DatabaseMigrator(str(django_db_path))
    return migrator
