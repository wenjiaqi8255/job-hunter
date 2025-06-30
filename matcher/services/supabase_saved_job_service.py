from supabase import Client
from datetime import datetime
from typing import Optional

# 注意：get_supabase_client 已被移除。
# 所有函数现在都希望接收一个已认证的 supabase 客户端实例，并依赖 RLS 策略。

# 查询单条申请记录
def get_supabase_saved_job(supabase: Client, original_job_id: str):
    # user_id 不再需要作为参数，RLS 会自动处理
    resp = supabase.table('saved_jobs').select('*').eq('original_job_id', original_job_id).execute()
    # 如果 RLS 生效且没有找到匹配当前用户的记录，data 会是空列表
    data = resp.data if hasattr(resp, 'data') and resp.data else None
    if data:
        return data[0]
    return None

# 创建申请记录（含岗位快照）
def create_supabase_saved_job(supabase: Client, data: dict):
    # user_id 会由 RLS 策略根据 JWT 自动填充或验证，无需在 data 中提供
    if 'user_id' in data:
        # 最好从数据中移除，以防混淆
        del data['user_id']

    if 'original_job_id' not in data:
        raise ValueError("Missing required field 'original_job_id' in saved_job data")
    
    # 确保 created_at 和 updated_at 存在
    now = datetime.utcnow().isoformat()
    data.setdefault('created_at', now)
    data.setdefault('updated_at', now)

    resp = supabase.table('saved_jobs').insert(data).execute()
    return resp.data[0] if hasattr(resp, 'data') and resp.data else None

# 更新申请状态和备注
def update_supabase_saved_job_status(supabase: Client, original_job_id: str, new_status=None, notes=None):
    update_data = {}
    if new_status:
        update_data['status'] = new_status
    if notes is not None:
        update_data['notes'] = notes
    
    if not update_data:
        return None # Nothing to update

    update_data['updated_at'] = datetime.utcnow().isoformat()
    # user_id 条件被移除，RLS 会确保只更新属于当前用户的记录
    resp = supabase.table('saved_jobs').update(update_data).eq('original_job_id', original_job_id).execute()
    return resp.data[0] if hasattr(resp, 'data') and resp.data else None

# 查询所有申请记录（可选按状态过滤）
def list_supabase_saved_jobs(supabase: Client, status: Optional[str] = None):
    # user_id 条件被移除，RLS 会自动过滤
    query = supabase.table('saved_jobs').select('*')
    if status:
        query = query.eq('status', status)
    resp = query.order('updated_at', desc=True).execute()
    return resp.data if hasattr(resp, 'data') else []