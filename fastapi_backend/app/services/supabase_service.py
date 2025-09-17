"""
Supabase服务模块
基于Django的job_listing_service.py重构
"""
from typing import List, Dict, Optional
from datetime import datetime, date, time
from supabase import Client, create_client

from ..core.config import settings

def create_supabase_client() -> Optional[Client]:
    """创建Supabase客户端"""
    if not settings.supabase_url or not settings.supabase_key:
        print("ERROR: Supabase URL or key not configured")
        return None
    
    try:
        supabase = create_client(settings.supabase_url, settings.supabase_key)
        return supabase
    except Exception as e:
        print(f"ERROR: Could not create Supabase client: {e}")
        return None

def fetch_todays_job_listings_from_supabase(supabase: Client) -> List[Dict]:
    """
    从Supabase获取今日创建的工作职位
    对应Django的fetch_todays_job_listings_from_supabase
    """
    if not supabase:
        print("ERROR: Supabase client not available in fetch_todays_job_listings_from_supabase.")
        return []
    
    try:
        today = date.today()
        start_of_day = datetime.combine(today, time.min).isoformat()
        end_of_day = datetime.combine(today, time.max).isoformat()

        # 假设表名为 'job_listings'
        response = supabase.table('job_listings').select('*').gte('created_at', start_of_day).lte('created_at', end_of_day).execute()
        
        if response.data:
            return response.data
        return []
    except Exception as e:
        print(f"ERROR: Could not fetch today's job listings from Supabase: {e}")
        return []

def fetch_anomaly_analysis_for_jobs_from_supabase(supabase: Client, job_ids: List[str]) -> Dict[str, Dict]:
    """
    从Supabase获取工作的异常分析数据
    对应Django的fetch_anomaly_analysis_for_jobs_from_supabase
    """
    if not supabase or not job_ids:
        if not supabase:
            print("ERROR: Supabase client not available in fetch_anomaly_analysis_for_jobs_from_supabase.")
        return {}
    
    try:
        # job_ids是UUID，应该转换为字符串
        str_job_ids = [str(job_id) for job_id in job_ids]
        
        # 假设表名为 'job_anomaly_analysis'
        response = supabase.table('job_anomaly_analysis').select('*').in_('job_listing_id', str_job_ids).execute()
        
        if response.data:
            # 返回job_id -> anomaly_data的映射
            return {item['job_listing_id']: item for item in response.data}
        return {}
    except Exception as e:
        print(f"ERROR: Could not fetch anomaly analysis from Supabase for jobs {job_ids}: {e}")
        return {}

def fetch_job_listings_by_ids(supabase: Client, job_ids: List[str]) -> List[Dict]:
    """
    根据ID列表从Supabase获取工作职位
    """
    if not supabase or not job_ids:
        return []
    
    try:
        str_job_ids = [str(job_id) for job_id in job_ids]
        response = supabase.table('job_listings').select('*').in_('id', str_job_ids).execute()
        
        if response.data:
            return response.data
        return []
    except Exception as e:
        print(f"ERROR: Could not fetch job listings by IDs from Supabase: {e}")
        return []

def create_job_listing_in_supabase(supabase: Client, job_data: Dict) -> Optional[Dict]:
    """
    在Supabase中创建新的工作职位
    """
    if not supabase:
        print("ERROR: Supabase client not available")
        return None
    
    try:
        response = supabase.table('job_listings').insert(job_data).execute()
        
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"ERROR: Could not create job listing in Supabase: {e}")
        return None

def update_job_listing_in_supabase(supabase: Client, job_id: str, job_data: Dict) -> Optional[Dict]:
    """
    在Supabase中更新工作职位
    """
    if not supabase:
        print("ERROR: Supabase client not available")
        return None
    
    try:
        response = supabase.table('job_listings').update(job_data).eq('id', job_id).execute()
        
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"ERROR: Could not update job listing in Supabase: {e}")
        return None

def delete_job_listing_in_supabase(supabase: Client, job_id: str) -> bool:
    """
    从Supabase中删除工作职位
    """
    if not supabase:
        print("ERROR: Supabase client not available")
        return False
    
    try:
        response = supabase.table('job_listings').delete().eq('id', job_id).execute()
        return True
    except Exception as e:
        print(f"ERROR: Could not delete job listing in Supabase: {e}")
        return False

def search_job_listings_in_supabase(
    supabase: Client,
    query: Optional[str] = None,
    industry: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """
    在Supabase中搜索工作职位
    """
    if not supabase:
        print("ERROR: Supabase client not available")
        return []
    
    try:
        # 构建查询
        supabase_query = supabase.table('job_listings').select('*')
        
        if industry:
            supabase_query = supabase_query.eq('industry', industry)
        
        if location:
            supabase_query = supabase_query.ilike('location', f'%{location}%')
        
        if query:
            # 在标题或描述中搜索
            supabase_query = supabase_query.or_(f'job_title.ilike.%{query}%,description.ilike.%{query}%')
        
        # 限制结果数量
        supabase_query = supabase_query.limit(limit)
        
        response = supabase_query.execute()
        
        if response.data:
            return response.data
        return []
    except Exception as e:
        print(f"ERROR: Could not search job listings in Supabase: {e}")
        return []
