from supabase import Client

# 注意：所有函数现在都依赖于通过认证的 Supabase 客户端中包含的 JWT 来实施 RLS。
# 不再需要传递 User 对象或在查询中手动指定 user_id。

def get_user_experiences(supabase: Client) -> list:
    """Fetches all work experiences for the authenticated user from Supabase."""
    if not supabase:
        return []

    try:
        # RLS 策略将根据客户端的 JWT 自动将结果范围限定为当前用户。
        # 不再需要 .eq('user_id', user_id)
        response = supabase.table('work_experiences') \
            .select('*') \
            .order('created_at', desc=True) \
            .execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching user experiences from Supabase: {e}")
        return []

def delete_experience(supabase: Client, experience_id: str):
    """Deletes a specific work experience for the authenticated user from Supabase."""
    if not supabase:
        raise Exception("Supabase client not available.")

    try:
        # RLS 策略将确保用户只能删除自己的经历。
        # 不再需要 .eq('user_id', user.username)
        response = supabase.table('work_experiences') \
            .delete() \
            .eq('id', experience_id) \
            .execute()
        
        # 检查 response.data 是否为空，可以判断删除是否成功（或被 RLS 阻止）
        if not response.data:
            # This might happen if the RLS policy prevents the deletion or the item doesn't exist.
            raise Exception("Failed to delete experience. Check permissions or if the item exists.")
            
        return response.data
    except Exception as e:
        print(f"Error deleting experience from Supabase: {e}")
        raise e