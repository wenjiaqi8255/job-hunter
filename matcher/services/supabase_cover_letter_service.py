"""
Supabase Cover Letter 服务
管理求职信的 Supabase 数据操作
"""
from supabase import Client
from datetime import datetime
from typing import Optional, List, Dict, Any


def get_supabase_cover_letter(supabase: Client, original_job_id: str) -> Optional[Dict[str, Any]]:
    """获取指定职位的求职信"""
    try:
        resp = supabase.table('cover_letters').select('*').eq('original_job_id', str(original_job_id)).execute()
        data = resp.data if hasattr(resp, 'data') and resp.data else None
        if data:
            return data[0]
        return None
    except Exception as e:
        print(f"Error fetching cover letter for job {original_job_id}: {e}")
        return None


def create_supabase_cover_letter(supabase: Client, data: dict) -> Optional[Dict[str, Any]]:
    """创建求职信记录"""
    try:
        # 确保必要字段存在
        if 'original_job_id' not in data:
            raise ValueError("Missing required field 'original_job_id'")
        
        # 设置时间戳
        now = datetime.utcnow().isoformat()
        data.setdefault('created_at', now)
        data.setdefault('updated_at', now)
        
        # 确保 original_job_id 是字符串
        data['original_job_id'] = str(data['original_job_id'])
        
        resp = supabase.table('cover_letters').insert(data).execute()
        return resp.data[0] if hasattr(resp, 'data') and resp.data else None
    except Exception as e:
        print(f"Error creating cover letter: {e}")
        return None


def update_supabase_cover_letter(supabase: Client, original_job_id: str, content: str) -> Optional[Dict[str, Any]]:
    """更新求职信内容"""
    try:
        update_data = {
            'content': content,
            'updated_at': datetime.utcnow().isoformat()
        }
        resp = supabase.table('cover_letters').update(update_data).eq('original_job_id', str(original_job_id)).execute()
        return resp.data[0] if hasattr(resp, 'data') and resp.data else None
    except Exception as e:
        print(f"Error updating cover letter for job {original_job_id}: {e}")
        return None


def upsert_supabase_cover_letter(supabase: Client, data: dict) -> Optional[Dict[str, Any]]:
    """创建或更新求职信（upsert 操作）"""
    try:
        # 确保必要字段存在
        if 'original_job_id' not in data:
            raise ValueError("Missing required field 'original_job_id'")
        
        # 设置时间戳
        now = datetime.utcnow().isoformat()
        data['updated_at'] = now
        data.setdefault('created_at', now)
        
        # 确保 original_job_id 是字符串
        data['original_job_id'] = str(data['original_job_id'])
        
        resp = supabase.table('cover_letters').upsert(data, on_conflict='user_id,original_job_id').execute()
        return resp.data[0] if hasattr(resp, 'data') and resp.data else None
    except Exception as e:
        print(f"Error upserting cover letter: {e}")
        return None


def list_supabase_cover_letters_for_jobs(supabase: Client, job_ids: List[str]) -> List[str]:
    """批量查询多个职位的求职信状态，返回有求职信的 job_id 列表"""
    try:
        if not job_ids:
            return []
        
        # 确保所有 job_ids 都是字符串
        job_ids_str = [str(job_id) for job_id in job_ids]
        
        resp = supabase.table('cover_letters').select('original_job_id').in_('original_job_id', job_ids_str).execute()
        return [item['original_job_id'] for item in resp.data] if resp.data else []
    except Exception as e:
        print(f"Error fetching cover letters for jobs {job_ids}: {e}")
        return []


def delete_supabase_cover_letter(supabase: Client, original_job_id: str) -> bool:
    """删除求职信"""
    try:
        resp = supabase.table('cover_letters').delete().eq('original_job_id', str(original_job_id)).execute()
        return True
    except Exception as e:
        print(f"Error deleting cover letter for job {original_job_id}: {e}")
        return False
