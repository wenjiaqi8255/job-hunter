import os
from django.conf import settings
from supabase import create_client
from datetime import datetime

def get_supabase_client():
    url = os.environ.get('SUPABASE_URL') or getattr(settings, 'SUPABASE_URL', None)
    key = os.environ.get('SUPABASE_KEY') or getattr(settings, 'SUPABASE_KEY', None)
    if not url or not key:
        raise Exception('Supabase URL/KEY 未配置')
    return create_client(url, key)

# 查询单条申请记录
def get_supabase_saved_job(user_session_key, original_job_id):
    supabase = get_supabase_client()
    resp = supabase.table('saved_jobs').select('*').eq('user_session_key', user_session_key).eq('original_job_id', original_job_id).execute()
    data = resp.data if hasattr(resp, 'data') else None
    if data and isinstance(data, list) and len(data) > 0:
        return data[0]
    return None

# 创建申请记录（含岗位快照）
def create_supabase_saved_job(data):
    supabase = get_supabase_client()
    resp = supabase.table('saved_jobs').insert(data).execute()
    return resp.data if hasattr(resp, 'data') else None

# 更新申请状态和备注
def update_supabase_saved_job_status(user_session_key, original_job_id, new_status=None, notes=None):
    supabase = get_supabase_client()
    update_data = {}
    if new_status:
        update_data['status'] = new_status
    if notes is not None:
        update_data['notes'] = notes
    update_data['updated_at'] = datetime.utcnow().isoformat()
    resp = supabase.table('saved_jobs').update(update_data).eq('user_session_key', user_session_key).eq('original_job_id', original_job_id).execute()
    return resp.data if hasattr(resp, 'data') else None

# 查询所有申请记录（可选按状态过滤）
def list_supabase_saved_jobs(user_session_key, status=None):
    supabase = get_supabase_client()
    query = supabase.table('saved_jobs').select('*').eq('user_session_key', user_session_key)
    if status:
        query = query.eq('status', status)
    resp = query.order('updated_at', desc=True).execute()
    return resp.data if hasattr(resp, 'data') else [] 