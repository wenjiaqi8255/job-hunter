import os
from django.core.management.base import BaseCommand
from django.conf import settings
from matcher.models import SavedJob
from supabase import create_client
from django.db import transaction
from dotenv import load_dotenv

class Command(BaseCommand):
    help = 'Migrate all local SavedJob records to Supabase saved_jobs table.'

    def handle(self, *args, **options):
        # 加载 .env 文件（如果存在）
        load_dotenv()
        supabase_url = os.environ.get('SUPABASE_URL') or getattr(settings, 'SUPABASE_URL', None)
        supabase_key = os.environ.get('SUPABASE_KEY') or getattr(settings, 'SUPABASE_KEY', None)
        if not supabase_url or not supabase_key:
            self.stderr.write(self.style.ERROR('Supabase URL/KEY 未配置，请检查 .env 或 settings.py'))
            return
        supabase = create_client(supabase_url, supabase_key)

        saved_jobs = SavedJob.objects.select_related('job_listing').all()
        total = saved_jobs.count()
        self.stdout.write(f'共发现 {total} 条 SavedJob 记录，开始迁移...')
        migrated = 0
        errors = 0
        for sj in saved_jobs:
            job = sj.job_listing
            data = {
                "user_session_key": sj.user_session_key,
                "status": sj.status,
                "applied_at": sj.created_at.isoformat(),
                "notes": sj.notes,
                "original_job_id": job.id,
                "company_name": job.company_name,
                "job_title": job.job_title,
                "job_description": job.description,
                "application_url": job.application_url,
                "location": job.location,
                "salary_range": job.salary_range,
                "industry": job.industry,
                "created_at": sj.created_at.isoformat(),
                "updated_at": sj.updated_at.isoformat(),
            }
            try:
                # 唯一约束冲突时跳过
                response = supabase.table("saved_jobs").insert(data).execute()
                if hasattr(response, 'status_code') and response.status_code >= 400:
                    self.stderr.write(self.style.WARNING(f"迁移失败: {data['original_job_id']} - {response}"))
                    errors += 1
                else:
                    migrated += 1
            except Exception as e:
                self.stderr.write(self.style.WARNING(f"迁移失败: {data['original_job_id']} - {e}"))
                errors += 1
        self.stdout.write(self.style.SUCCESS(f'迁移完成！成功 {migrated} 条，失败 {errors} 条。')) 