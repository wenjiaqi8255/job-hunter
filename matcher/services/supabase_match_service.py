"""
纯Supabase匹配历史服务
一步到位迁移，删除Django双写复杂性
直接使用Supabase + JSONB结构
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging

from .supabase_auth_helper import create_authed_supabase_client

logger = logging.getLogger(__name__)


class SupabaseMatchService:
    """纯Supabase匹配历史服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def save_match_session(self, session_data: Dict[str, Any], user_jwt_token: str) -> Dict[str, Any]:
        """
        保存匹配会话到Supabase
        直接使用AI生成的JSONB结构，不做转换
        
        Args:
            session_data: 匹配会话数据，包含AI生成的jobs数据
            user_jwt_token: 用户JWT token
            
        Returns:
            Dict: 保存结果
        """
        try:
            supabase_client = create_authed_supabase_client(user_jwt_token)
            
            # 1. 保存匹配会话
            session_record = {
                'id': str(uuid.uuid4()),
                'user_id': session_data['user_id'],
                'skills_text': session_data.get('skills_text', ''),
                'user_preferences_text': session_data.get('user_preferences_text', ''),
                'structured_user_profile_json': session_data.get('structured_user_profile_json', {}),
                'matched_at': datetime.now(timezone.utc).isoformat(),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            session_response = supabase_client.table('match_sessions').insert(session_record).execute()
            
            if not session_response.data:
                raise Exception("Failed to save match session")
            
            session_id = session_response.data[0]['id']
            self.logger.info(f"Saved match session {session_id}")
            
            # 2. 保存匹配工作（直接使用AI的JSONB输出）
            saved_jobs = 0
            if 'jobs' in session_data:
                for job_data in session_data['jobs']:
                    if self._save_matched_job(job_data, session_id, supabase_client):
                        saved_jobs += 1
            
            return {
                'success': True,
                'session_id': session_id,
                'saved_jobs': saved_jobs,
                'message': f'Saved session with {saved_jobs} jobs'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to save match session: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'session_id': None,
                'saved_jobs': 0
            }
    
    def get_latest_match(self, user_id: str, user_jwt_token: str) -> Dict[str, Any]:
        """
        获取用户最新的匹配结果
        直接从Supabase返回JSONB数据
        
        Args:
            user_id: 用户ID
            user_jwt_token: 用户JWT token
            
        Returns:
            Dict: 最新匹配结果
        """
        try:
            supabase_client = create_authed_supabase_client(user_jwt_token)
            
            # 获取最新的匹配会话
            session_response = supabase_client.table('match_sessions').select(
                'id, matched_at, created_at'
            ).eq('user_id', user_id).order('matched_at', desc=True).limit(1).execute()
            
            if not session_response.data:
                return {
                    'success': True,
                    'jobs': [],
                    'count': 0,
                    'message': 'No match history found',
                    'user_id': user_id,
                    'session_id': None,
                    'matched_at': None
                }
            
            latest_session = session_response.data[0]
            session_id = latest_session['id']
            
            # 获取该会话的所有匹配工作
            jobs_response = supabase_client.table('matched_jobs').select(
                'job_id, score, status, analysis, application_tips, created_at'
            ).eq('match_session_id', session_id).order('score', desc=True).execute()
            
            # 获取工作基础信息并组合数据
            jobs_data = []
            for job in jobs_response.data or []:
                # 获取工作详情
                job_info = self._get_job_details(job['job_id'], supabase_client)
                
                # 组合完整的工作数据
                complete_job = {
                    'id': job['job_id'],
                    'job_id': job['job_id'],
                    'score': job.get('score', 0),
                    'status': job.get('status', 'new'),
                    
                    # JSONB结构化数据（直接来自AI）
                    'analysis': job.get('analysis', {}),
                    'application_tips': job.get('application_tips', {}),
                    
                    # 工作基础信息
                    'title': job_info.get('job_title', 'Unknown'),
                    'company': job_info.get('company_name', 'Unknown'),
                    'location': job_info.get('location', ''),
                    'level': job_info.get('level', ''),
                    'industry': job_info.get('industry', ''),
                    'flexibility': job_info.get('flexibility', ''),
                    'salaryRange': job_info.get('salary_range', ''),
                    'description': job_info.get('description', ''),
                    'applicationUrl': job_info.get('application_url', ''),
                    
                    # 时间戳
                    'created_at': job.get('created_at', ''),
                    'updated_at': job.get('created_at', ''),
                    
                    # 向后兼容字段
                    'matchScore': job.get('score', 0),
                    'matchReason': job.get('analysis', {}).get('reasoning', ''),
                }
                
                jobs_data.append(complete_job)
            
            return {
                'success': True,
                'jobs': jobs_data,
                'count': len(jobs_data),
                'user_id': user_id,
                'session_id': session_id,
                'matched_at': latest_session.get('matched_at', '')
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get latest match: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'jobs': [],
                'count': 0,
                'user_id': user_id
            }
    
    def get_match_history(self, user_id: str, user_jwt_token: str, limit: int = 10) -> Dict[str, Any]:
        """
        获取用户匹配历史
        
        Args:
            user_id: 用户ID
            user_jwt_token: 用户JWT token
            limit: 返回记录数限制
            
        Returns:
            Dict: 匹配历史数据
        """
        try:
            supabase_client = create_authed_supabase_client(user_jwt_token)
            
            # 获取匹配会话
            sessions_response = supabase_client.table('match_sessions').select(
                'id, skills_text, user_preferences_text, structured_user_profile_json, matched_at, created_at'
            ).eq('user_id', user_id).order('matched_at', desc=True).limit(limit).execute()
            
            if not sessions_response.data:
                return {
                    'success': True,
                    'sessions': [],
                    'count': 0,
                    'message': 'No match history found'
                }
            
            # 为每个会话获取匹配的工作
            enriched_sessions = []
            for session in sessions_response.data:
                jobs_response = supabase_client.table('matched_jobs').select(
                    'job_id, score, status, analysis, application_tips, created_at'
                ).eq('match_session_id', session['id']).order('score', desc=True).execute()
                
                # 转换为前端期望的格式
                matched_jobs = []
                for job in jobs_response.data or []:
                    job_info = self._get_job_details(job['job_id'], supabase_client)
                    
                    complete_job = {
                        'id': job['job_id'],
                        'job_id': job['job_id'],
                        'score': job.get('score', 0),
                        'status': job.get('status', 'new'),
                        'analysis': job.get('analysis', {}),
                        'application_tips': job.get('application_tips', {}),
                        'title': job_info.get('job_title', 'Unknown'),
                        'company': job_info.get('company_name', 'Unknown'),
                        'location': job_info.get('location', ''),
                        'level': job_info.get('level', ''),
                        'industry': job_info.get('industry', ''),
                        'flexibility': job_info.get('flexibility', ''),
                        'salaryRange': job_info.get('salary_range', ''),
                        'description': job_info.get('description', ''),
                        'applicationUrl': job_info.get('application_url', ''),
                        'created_at': job.get('created_at', ''),
                        'updated_at': job.get('created_at', ''),
                    }
                    
                    matched_jobs.append(complete_job)
                
                session['matched_jobs'] = matched_jobs
                enriched_sessions.append(session)
            
            return {
                'success': True,
                'sessions': enriched_sessions,
                'count': len(enriched_sessions)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get match history: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'sessions': []
            }
    
    def update_job_status(self, job_id: str, status: str, user_jwt_token: str) -> Dict[str, Any]:
        """
        更新工作匹配状态
        
        Args:
            job_id: 工作ID
            status: 新状态
            user_jwt_token: 用户JWT token
            
        Returns:
            Dict: 更新结果
        """
        try:
            supabase_client = create_authed_supabase_client(user_jwt_token)
            
            response = supabase_client.table('matched_jobs').update({
                'status': status,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('job_id', job_id).execute()
            
            if response.data:
                return {
                    'success': True,
                    'message': f'Updated job {job_id} status to {status}'
                }
            else:
                return {
                    'success': False,
                    'error': 'No matching job found'
                }
                
        except Exception as e:
            self.logger.error(f"Failed to update job status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _save_matched_job(self, job_data: Dict[str, Any], session_id: str, supabase_client) -> bool:
        """
        保存单个匹配工作到Supabase
        直接使用AI生成的JSONB数据
        """
        try:
            job_record = {
                'id': str(uuid.uuid4()),
                'match_session_id': session_id,
                'job_id': str(job_data['job']['id']),
                'score': job_data.get('score', 0),
                'status': 'new',
                # 直接使用AI的JSONB输出，不做转换
                'analysis': job_data.get('analysis', {}),
                'application_tips': job_data.get('application_tips', {}),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            response = supabase_client.table('matched_jobs').insert(job_record).execute()
            
            if response.data:
                self.logger.info(f"Saved matched job {job_data['job']['id']}")
                return True
            else:
                self.logger.error(f"Failed to save matched job {job_data['job']['id']}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error saving matched job: {str(e)}")
            return False
    
    def _get_job_details(self, job_id: str, supabase_client) -> Dict[str, Any]:
        """获取工作详情"""
        try:
            response = supabase_client.table('job_listings').select('*').eq('id', job_id).execute()
            
            if response.data:
                return response.data[0]
            else:
                self.logger.warning(f"Job {job_id} not found in job_listings")
                return {}
                
        except Exception as e:
            self.logger.warning(f"Failed to fetch job details for {job_id}: {str(e)}")
            return {}
    
    def get_session_by_id(self, session_id: str, user_id: str, user_jwt_token: str) -> Dict[str, Any]:
        """
        通过会话ID获取特定会话的详细信息
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            user_jwt_token: 用户JWT token
            
        Returns:
            Dict: 会话详情
        """
        try:
            supabase_client = create_authed_supabase_client(user_jwt_token)
            
            # 获取会话基本信息
            session_response = supabase_client.table('match_sessions').select('*').eq('id', session_id).eq('user_id', user_id).execute()
            
            if not session_response.data:
                return {
                    'success': False,
                    'error': 'Session not found or access denied'
                }
            
            session = session_response.data[0]
            
            # 获取该会话的匹配工作
            matched_jobs_response = supabase_client.table('matched_jobs').select(
                'id, job_id, score, status, analysis, application_tips, created_at'
            ).eq('match_session_id', session_id).execute()
            
            matched_jobs = []
            for job in matched_jobs_response.data:
                # 获取工作基本信息
                job_listing_response = supabase_client.table('job_listings').select('*').eq('id', job['job_id']).execute()
                
                job_data = {
                    'id': job['id'],
                    'job_id': job['job_id'],
                    'score': job['score'],
                    'status': job['status'],
                    'analysis': job.get('analysis', {}),
                    'application_tips': job.get('application_tips', {}),
                    'created_at': job['created_at']
                }
                
                # 添加工作基本信息
                if job_listing_response.data:
                    job_listing = job_listing_response.data[0]
                    job_data['job_listing'] = job_listing
                
                matched_jobs.append(job_data)
            
            # 将匹配工作添加到会话数据中
            session['matched_jobs'] = matched_jobs
            
            return {
                'success': True,
                'session': session
            }
            
        except Exception as e:
            self.logger.error(f"获取会话详情时出错: {str(e)}")
            return {
                'success': False,
                'error': f'获取会话详情时出错: {str(e)}'
            }


# 单例实例
supabase_match_service = SupabaseMatchService()
