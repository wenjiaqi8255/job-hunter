#!/usr/bin/env python3
"""
FastAPI开发环境数据初始化脚本
将Django initial_data.json 转换为FastAPI格式并导入数据库
遵循KISS原则：简单直接的转换逻辑，不增加复杂度
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.database import Base, SessionLocal
from app.models import User, UserProfile, JobListing, MatchSession, MatchedJob, SavedJob, CoverLetter, CustomResume

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_datetime(datetime_str):
    """解析ISO格式 datetime字符串"""
    if not datetime_str:
        return None
    try:
        return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    except:
        return None

class DataMigrator:
    """数据迁移器 - 单一职责：数据转换和导入"""

    def __init__(self, db: Session):
        self.db = db
        self.user_mapping = {}  # Django user_id -> FastAPI user_id
        self.job_mapping = {}   # Django job_listing_id -> FastAPI job_listing_id

    def migrate_users(self, django_data: list) -> None:
        """迁移用户数据"""
        logger.info("开始迁移用户数据...")

        user_records = [item for item in django_data if item.get('model') == 'auth.user']

        for user_record in user_records:
            django_id = user_record['pk']
            fields = user_record['fields']

            # 检查用户是否已存在
            existing_user = self.db.query(User).filter(User.username == fields['username']).first()
            if existing_user:
                self.user_mapping[django_id] = existing_user.id
                continue

            # 创建新用户
            user = User(
                username=fields['username'],
                email=fields['email'],
                first_name=fields['first_name'],
                last_name=fields['last_name'],
                is_active=fields['is_active'],
                is_superuser=fields['is_superuser'],
                password=f"django_password_hash_{django_id}",  # Django密码哈希无法直接使用
                date_joined=parse_datetime(fields['date_joined']) or datetime.now()
            )

            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            self.user_mapping[django_id] = user.id
            logger.info(f"创建用户: {user.username} (ID: {user.id})")

    def migrate_user_profiles(self, django_data: list) -> None:
        """迁移用户档案数据"""
        logger.info("开始迁移用户档案数据...")

        profile_records = [item for item in django_data if item.get('model') == 'matcher.userprofile']

        for profile_record in profile_records:
            django_id = profile_record['pk']
            fields = profile_record['fields']

            # 获取对应的FastAPI用户ID
            # Django的userprofile通过user字段关联auth.user，需要找到对应的用户
            user_email = fields.get('user_email')
            if not user_email:
                continue

            user = self.db.query(User).filter(User.email == user_email).first()
            if not user:
                logger.warning(f"未找到用户邮箱: {user_email}")
                continue

            # 检查档案是否已存在
            existing_profile = self.db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
            if existing_profile:
                continue

            # 创建用户档案
            profile = UserProfile(
                user_id=user.id,
                user_cv_text=fields.get('user_cv_text'),
                cv_file=fields.get('cv_file', ''),
                user_preferences_text=fields.get('user_preferences_text'),
                created_at=parse_datetime(fields.get('created_at')) or datetime.now(),
                updated_at=parse_datetime(fields.get('updated_at')) or datetime.now()
            )

            self.db.add(profile)
            logger.info(f"创建用户档案: {user.email}")

        self.db.commit()

    def migrate_job_listings(self, django_data: list) -> None:
        """迁移工作职位数据"""
        logger.info("开始迁移工作职位数据...")

        job_records = [item for item in django_data if item.get('model') == 'matcher.joblisting']

        for job_record in job_records:
            django_id = job_record['pk']
            fields = job_record['fields']

            # 检查工作是否已存在
            existing_job = self.db.query(JobListing).filter(JobListing.job_title == fields['job_title']).first()
            if existing_job:
                self.job_mapping[django_id] = existing_job.id
                continue

            # 创建工作职位
            job = JobListing(
                id=django_id,  # Django的pk就是字符串ID
                company_name=fields['company_name'],
                job_title=fields['job_title'],
                location=fields['location'],
                description=fields['description'],
                industry=fields.get('industry', 'Not specified'),
                salary_range=fields.get('salary_range', 'Not specified'),
                application_url=fields.get('application_url'),
                flexibility=fields.get('flexibility'),
                level=fields.get('level'),
                created_at=parse_datetime(fields.get('created_at')) or datetime.now(),
                processed_at=parse_datetime(fields.get('processed_at'))
            )

            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)

            self.job_mapping[django_id] = job.id
            logger.info(f"创建工作职位: {job.job_title} (ID: {job.id})")

    def migrate_matched_jobs(self, django_data: list) -> None:
        """迁移匹配结果数据"""
        logger.info("开始迁移匹配结果数据...")

        matched_job_records = [item for item in django_data if item.get('model') == 'matcher.matchedjob']

        for matched_record in matched_job_records:
            fields = matched_record['fields']

            # 获取用户和工作ID
            user_email = fields.get('user_email')
            job_title = fields.get('job_title')

            if not user_email or not job_title:
                continue

            user = self.db.query(User).filter(User.email == user_email).first()
            job = self.db.query(JobListing).filter(JobListing.job_title == job_title).first()

            if not user or not job:
                logger.warning(f"未找到用户或工作: {user_email} - {job_title}")
                continue

            # 检查是否已存在
            existing_match = self.db.query(MatchedJob).filter(
                MatchedJob.user_id == user.id,
                MatchedJob.job_listing_id == job.id
            ).first()

            if existing_match:
                continue

            # 创建匹配结果
            matched_job = MatchedJob(
                user_id=user.id,
                job_listing_id=job.id,
                match_score=fields.get('match_score', 0.0),
                match_reasons=fields.get('match_reasons', ''),
                created_at=parse_datetime(fields.get('created_at')) or datetime.now(),
                updated_at=parse_datetime(fields.get('updated_at')) or datetime.now()
            )

            self.db.add(matched_job)
            logger.info(f"创建匹配结果: {user.email} - {job.job_title}")

        self.db.commit()

    def migrate_cover_letters(self, django_data: list) -> None:
        """迁移求职信数据"""
        logger.info("开始迁移求职信数据...")

        cover_letter_records = [item for item in django_data if item.get('model') == 'matcher.coverletter']

        for cover_record in cover_letter_records:
            fields = cover_record['fields']

            # 通过用户邮箱和工作标题查找
            user_email = fields.get('user_email')
            job_title = fields.get('job_title')

            if not user_email or not job_title:
                continue

            user = self.db.query(User).filter(User.email == user_email).first()
            job = self.db.query(JobListing).filter(JobListing.job_title == job_title).first()

            if not user or not job:
                continue

            # 检查是否已存在
            existing_letter = self.db.query(CoverLetter).filter(
                CoverLetter.user_id == user.id,
                CoverLetter.job_listing_id == job.id
            ).first()

            if existing_letter:
                continue

            # 创建求职信
            cover_letter = CoverLetter(
                user_id=user.id,
                job_listing_id=job.id,
                content=fields.get('content', ''),
                created_at=parse_datetime(fields.get('created_at')) or datetime.now(),
                updated_at=parse_datetime(fields.get('updated_at')) or datetime.now()
            )

            self.db.add(cover_letter)
            logger.info(f"创建求职信: {user.email} - {job.job_title}")

        self.db.commit()

    def migrate_custom_resumes(self, django_data: list) -> None:
        """迁移定制简历数据"""
        logger.info("开始迁移定制简历数据...")

        resume_records = [item for item in django_data if item.get('model') == 'matcher.customresume']

        for resume_record in resume_records:
            fields = resume_record['fields']

            # Django的user和job_listing是ID，需要映射
            django_user_id = fields.get('user')
            django_job_listing_id = fields.get('job_listing')

            fastapi_user_id = self.user_mapping.get(django_user_id)
            fastapi_job_listing_id = self.job_mapping.get(django_job_listing_id)

            if not fastapi_user_id or not fastapi_job_listing_id:
                continue

            # 检查是否已存在
            existing_resume = self.db.query(CustomResume).filter(
                CustomResume.user_id == fastapi_user_id,
                CustomResume.job_listing_id == fastapi_job_listing_id
            ).first()

            if existing_resume:
                continue

            # 创建定制简历
            custom_resume = CustomResume(
                user_id=fastapi_user_id,
                job_listing_id=fastapi_job_listing_id,
                content=fields.get('content', ''),
                created_at=parse_datetime(fields.get('created_at')) or datetime.now(),
                updated_at=parse_datetime(fields.get('updated_at')) or datetime.now()
            )

            self.db.add(custom_resume)
            logger.info(f"创建定制简历: User {fastapi_user_id} - Job {fastapi_job_listing_id}")

        self.db.commit()

    def migrate_all(self, django_data: list) -> None:
        """执行完整的数据迁移"""
        logger.info("开始执行完整数据迁移...")

        try:
            # 按依赖关系顺序迁移
            self.migrate_users(django_data)
            self.migrate_user_profiles(django_data)
            self.migrate_job_listings(django_data)
            self.migrate_matched_jobs(django_data)
            self.migrate_cover_letters(django_data)
            self.migrate_custom_resumes(django_data)

            logger.info("✅ 数据迁移完成!")

        except Exception as e:
            logger.error(f"❌ 数据迁移失败: {e}")
            self.db.rollback()
            raise


def main():
    """主函数"""
    logger.info("🚀 开始FastAPI数据初始化...")

    # 读取Django数据文件
    initial_data_path = Path("../initial_data.json")
    if not initial_data_path.exists():
        logger.error(f"❌ 找不到initial_data.json文件: {initial_data_path}")
        return

    try:
        with open(initial_data_path, 'r', encoding='utf-8') as f:
            django_data = json.load(f)
    except Exception as e:
        logger.error(f"❌ 读取initial_data.json失败: {e}")
        return

    # 创建数据库连接
    engine = create_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)

    # 创建数据库会话
    db = SessionLocal()

    try:
        # 执行数据迁移
        migrator = DataMigrator(db)
        migrator.migrate_all(django_data)

        logger.info("🎉 数据初始化成功完成!")
        logger.info("📊 迁移统计:")
        logger.info(f"  - 用户: {db.query(User).count()}")
        logger.info(f"  - 用户档案: {db.query(UserProfile).count()}")
        logger.info(f"  - 工作职位: {db.query(JobListing).count()}")
        logger.info(f"  - 匹配结果: {db.query(MatchedJob).count()}")
        logger.info(f"  - 求职信: {db.query(CoverLetter).count()}")
        logger.info(f"  - 定制简历: {db.query(CustomResume).count()}")

    except Exception as e:
        logger.error(f"❌ 数据初始化失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()