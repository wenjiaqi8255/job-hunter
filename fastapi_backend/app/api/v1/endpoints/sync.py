"""
数据同步API路由
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from app.services.data_sync_service import get_sync_service, DataSyncService
from app.core.database_migrator import get_migrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sync", tags=["data-sync"])

@router.get("/status")
async def get_sync_status():
    """获取数据同步状态"""
    try:
        migrator = get_migrator()
        
        # 验证Django数据库连接
        django_ok = migrator.verify_django_tables()
        
        return {
            "status": "healthy" if django_ok else "error",
            "django_connection": django_ok,
            "message": "Data sync service is operational"
        }
    except Exception as e:
        logger.error(f"Error checking sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate")
async def validate_data_consistency(
    sync_service: DataSyncService = Depends(get_sync_service)
):
    """验证数据一致性"""
    try:
        results = await sync_service.validate_data_consistency()
        return results
    except Exception as e:
        logger.error(f"Error validating data consistency: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/repair")
async def repair_data_issues(
    sync_service: DataSyncService = Depends(get_sync_service)
):
    """修复数据问题"""
    try:
        success = await sync_service.repair_data_issues()
        return {
            "status": "success" if success else "error",
            "message": "Data repair completed" if success else "Data repair failed"
        }
    except Exception as e:
        logger.error(f"Error repairing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tables/structure/{table_name}")
async def get_table_structure(table_name: str):
    """获取数据库表结构"""
    try:
        migrator = get_migrator()
        structure = migrator.get_table_structure(table_name)
        
        return {
            "table_name": table_name,
            "structure": structure
        }
    except Exception as e:
        logger.error(f"Error getting table structure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-connection")
async def test_database_connection():
    """测试数据库连接"""
    try:
        migrator = get_migrator()
        
        # 测试核心表
        core_tables = [
            'auth_user',
            'matcher_userprofile', 
            'matcher_joblisting',
            'matcher_savedjob'
        ]
        
        results = {}
        for table in core_tables:
            structure = migrator.get_table_structure(table)
            results[table] = {
                "exists": len(structure) > 0,
                "columns": len(structure)
            }
        
        return {
            "status": "success",
            "tables": results
        }
    except Exception as e:
        logger.error(f"Error testing database connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))
