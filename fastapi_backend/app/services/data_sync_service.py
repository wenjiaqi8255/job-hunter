"""
数据同步服务 - 确保Django和FastAPI系统数据一致性
"""
import asyncio
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

from app.core.database_migrator import get_migrator

logger = logging.getLogger(__name__)

class DataSyncService:
    """数据同步服务"""
    
    def __init__(self):
        self.migrator = get_migrator()
        
    async def sync_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> bool:
        """同步用户配置文件到Django数据库"""
        try:
            # 更新Django数据库中的用户配置
            conn = sqlite3.connect(self.migrator.django_db_path)
            cursor = conn.cursor()
            
            # 检查用户配置是否存在
            cursor.execute("""
                SELECT user_id FROM matcher_userprofile WHERE user_id = ?
            """, (user_id,))
            
            if cursor.fetchone():
                # 更新现有记录
                cursor.execute("""
                    UPDATE matcher_userprofile 
                    SET user_cv_text = ?, user_preferences_text = ?, 
                        user_email = ?, updated_at = ?
                    WHERE user_id = ?
                """, (
                    profile_data.get('user_cv_text'),
                    profile_data.get('user_preferences_text'),
                    profile_data.get('user_email'),
                    datetime.now().isoformat(),
                    user_id
                ))
            else:
                # 插入新记录
                cursor.execute("""
                    INSERT INTO matcher_userprofile 
                    (user_id, user_cv_text, user_preferences_text, 
                     user_email, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    profile_data.get('user_cv_text'),
                    profile_data.get('user_preferences_text'),
                    profile_data.get('user_email'),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
            logger.info(f"User profile synced for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing user profile: {e}")
            return False
    
    async def sync_saved_job(self, saved_job_data: Dict[str, Any]) -> bool:
        """同步保存的工作到Django数据库"""
        try:
            conn = sqlite3.connect(self.migrator.django_db_path)
            cursor = conn.cursor()
            
            # 检查记录是否存在
            cursor.execute("""
                SELECT id FROM matcher_savedjob 
                WHERE user_id = ? AND job_listing_id = ?
            """, (saved_job_data['user_id'], saved_job_data['job_listing_id']))
            
            if cursor.fetchone():
                # 更新现有记录
                cursor.execute("""
                    UPDATE matcher_savedjob 
                    SET status = ?, notes = ?, updated_at = ?
                    WHERE user_id = ? AND job_listing_id = ?
                """, (
                    saved_job_data.get('status'),
                    saved_job_data.get('notes'),
                    datetime.now().isoformat(),
                    saved_job_data['user_id'],
                    saved_job_data['job_listing_id']
                ))
            else:
                # 插入新记录
                cursor.execute("""
                    INSERT INTO matcher_savedjob 
                    (user_id, job_listing_id, status, notes, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    saved_job_data['user_id'],
                    saved_job_data['job_listing_id'],
                    saved_job_data.get('status'),
                    saved_job_data.get('notes'),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
            logger.info(f"Saved job synced for user {saved_job_data['user_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing saved job: {e}")
            return False
    
    async def sync_match_session(self, session_data: Dict[str, Any]) -> bool:
        """同步匹配会话到Django数据库"""
        try:
            conn = sqlite3.connect(self.migrator.django_db_path)
            cursor = conn.cursor()
            
            # 插入匹配会话
            cursor.execute("""
                INSERT OR REPLACE INTO matcher_matchsession 
                (id, user_id, skills_text, user_preferences_text, 
                 structured_user_profile_json, matched_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_data['id'],
                session_data.get('user_id'),
                session_data['skills_text'],
                session_data.get('user_preferences_text'),
                session_data.get('structured_user_profile_json'),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Match session synced: {session_data['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing match session: {e}")
            return False
    
    async def validate_data_consistency(self) -> Dict[str, Any]:
        """验证数据一致性"""
        try:
            conn = sqlite3.connect(self.migrator.django_db_path)
            cursor = conn.cursor()
            
            validation_results = {
                'status': 'success',
                'checks': {},
                'errors': []
            }
            
            # 检查用户配置文件完整性
            cursor.execute("""
                SELECT COUNT(*) FROM matcher_userprofile 
                WHERE user_cv_text IS NULL OR user_cv_text = ''
            """)
            empty_profiles = cursor.fetchone()[0]
            validation_results['checks']['empty_profiles'] = empty_profiles
            
            # 检查孤立的保存工作记录
            cursor.execute("""
                SELECT COUNT(*) FROM matcher_savedjob s
                LEFT JOIN matcher_joblisting j ON s.job_listing_id = j.id
                WHERE j.id IS NULL
            """)
            orphaned_jobs = cursor.fetchone()[0]
            validation_results['checks']['orphaned_saved_jobs'] = orphaned_jobs
            
            # 检查匹配会话完整性
            cursor.execute("""
                SELECT COUNT(*) FROM matcher_matchsession 
                WHERE skills_text IS NULL OR skills_text = ''
            """)
            incomplete_sessions = cursor.fetchone()[0]
            validation_results['checks']['incomplete_sessions'] = incomplete_sessions
            
            if empty_profiles > 0:
                validation_results['errors'].append(f"{empty_profiles} empty user profiles found")
            
            if orphaned_jobs > 0:
                validation_results['errors'].append(f"{orphaned_jobs} orphaned saved jobs found")
                
            if incomplete_sessions > 0:
                validation_results['errors'].append(f"{incomplete_sessions} incomplete match sessions found")
            
            conn.close()
            logger.info("Data consistency validation completed")
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating data consistency: {e}")
            return {
                'status': 'error',
                'checks': {},
                'errors': [str(e)]
            }
    
    async def repair_data_issues(self) -> bool:
        """修复发现的数据问题"""
        try:
            conn = sqlite3.connect(self.migrator.django_db_path)
            cursor = conn.cursor()
            
            # 清理孤立的保存工作记录
            cursor.execute("""
                DELETE FROM matcher_savedjob 
                WHERE job_listing_id NOT IN (
                    SELECT id FROM matcher_joblisting
                )
            """)
            
            # 清理空的匹配会话
            cursor.execute("""
                DELETE FROM matcher_matchsession 
                WHERE skills_text IS NULL OR skills_text = ''
            """)
            
            conn.commit()
            conn.close()
            logger.info("Data repair completed")
            return True
            
        except Exception as e:
            logger.error(f"Error repairing data: {e}")
            return False

# 全局同步服务实例
sync_service = DataSyncService()

def get_sync_service() -> DataSyncService:
    """获取数据同步服务实例"""
    return sync_service
