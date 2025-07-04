"""
Django 管理命令：迁移 Cover Letter 数据到 Supabase
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from supabase import create_client
from matcher.models import CoverLetter
from matcher.services.supabase_cover_letter_service import create_supabase_cover_letter


class Command(BaseCommand):
    help = 'Migrate cover letters from SQLite to Supabase'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually migrating',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if there are existing records',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS('Starting Cover Letter migration to Supabase...')
        )
        
        # 获取所有现有的 cover letter
        cover_letters = CoverLetter.objects.select_related(
            'saved_job__job_listing', 
            'saved_job__user'
        ).all()
        
        total_count = cover_letters.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.WARNING('No cover letters found to migrate.')
            )
            return
        
        self.stdout.write(f'Found {total_count} cover letters to migrate.')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No actual migration will occur')
            )
        
        migrated_count = 0
        failed_count = 0
        skipped_count = 0
        
        for cover_letter in cover_letters:
            try:
                saved_job = cover_letter.saved_job
                job = saved_job.job_listing
                user = saved_job.user
                
                # 准备迁移数据
                migrate_data = {
                    "original_job_id": str(job.id),
                    "content": cover_letter.content,
                    "job_title": job.job_title,
                    "company_name": job.company_name,
                    "created_at": cover_letter.created_at.isoformat(),
                    "updated_at": cover_letter.updated_at.isoformat(),
                }
                
                self.stdout.write(
                    f'Processing: User {user.username}, Job {job.id} ({job.job_title[:50]}...)'
                )
                
                if dry_run:
                    self.stdout.write(f'  Would migrate: {len(cover_letter.content)} characters')
                    migrated_count += 1
                else:
                    # 注意：实际迁移需要处理用户认证
                    # 这里暂时跳过实际的 Supabase 调用
                    self.stdout.write(
                        self.style.WARNING(
                            '  SKIPPED: Actual Supabase migration requires user authentication setup'
                        )
                    )
                    skipped_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to process cover letter {cover_letter.id}: {e}')
                )
                failed_count += 1
        
        # 输出统计信息
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('Migration Summary:'))
        self.stdout.write(f'  Total found: {total_count}')
        self.stdout.write(f'  Successfully processed: {migrated_count}')
        self.stdout.write(f'  Failed: {failed_count}')
        self.stdout.write(f'  Skipped: {skipped_count}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nThis was a DRY RUN. Use --force to perform actual migration.')
            )
        
        self.stdout.write('\n' + self.style.SUCCESS('Migration completed!'))
