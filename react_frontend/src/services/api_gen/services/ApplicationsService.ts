/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CoverLetter } from '../models/CoverLetter';
import type { CoverLetterCreate } from '../models/CoverLetterCreate';
import type { CustomResume } from '../models/CustomResume';
import type { CustomResumeCreate } from '../models/CustomResumeCreate';
import type { SavedJob } from '../models/SavedJob';
import type { SavedJobCreate } from '../models/SavedJobCreate';
import type { SavedJobUpdate } from '../models/SavedJobUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ApplicationsService {
    /**
     * Get User Saved Jobs
     * 获取用户保存的工作申请
     * 对应Django的my_applications_page
     * @param userId
     * @param status
     * @param skip
     * @param limit
     * @returns SavedJob Successful Response
     * @throws ApiError
     */
    public static getUserSavedJobsApiV1ApplicationsSavedJobsGet(
        userId: number,
        status?: (string | null),
        skip?: number,
        limit: number = 100,
    ): CancelablePromise<Array<SavedJob>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/applications/saved-jobs',
            query: {
                'user_id': userId,
                'status': status,
                'skip': skip,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Save Job Application
     * 保存工作申请
     * 对应Django的job_detail_page POST请求
     * @param requestBody
     * @returns SavedJob Successful Response
     * @throws ApiError
     */
    public static saveJobApplicationApiV1ApplicationsSavedJobsPost(
        requestBody: SavedJobCreate,
    ): CancelablePromise<SavedJob> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/applications/saved-jobs',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Saved Job Status
     * 更新保存工作的状态
     * 对应Django的update_job_application_status
     * @param savedJobId
     * @param requestBody
     * @returns SavedJob Successful Response
     * @throws ApiError
     */
    public static updateSavedJobStatusApiV1ApplicationsSavedJobsSavedJobIdPut(
        savedJobId: number,
        requestBody: SavedJobUpdate,
    ): CancelablePromise<SavedJob> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/applications/saved-jobs/{saved_job_id}',
            path: {
                'saved_job_id': savedJobId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Saved Job
     * 删除保存的工作申请
     * @param savedJobId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteSavedJobApiV1ApplicationsSavedJobsSavedJobIdDelete(
        savedJobId: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/applications/saved-jobs/{saved_job_id}',
            path: {
                'saved_job_id': savedJobId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Generate Cover Letter
     * 生成求职信
     * 对应Django的generate_cover_letter_page
     * @param requestBody
     * @returns CoverLetter Successful Response
     * @throws ApiError
     */
    public static generateCoverLetterApiV1ApplicationsCoverLettersPost(
        requestBody: CoverLetterCreate,
    ): CancelablePromise<CoverLetter> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/applications/cover-letters',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Cover Letter
     * 获取求职信
     * @param savedJobId
     * @returns CoverLetter Successful Response
     * @throws ApiError
     */
    public static getCoverLetterApiV1ApplicationsCoverLettersSavedJobIdGet(
        savedJobId: number,
    ): CancelablePromise<CoverLetter> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/applications/cover-letters/{saved_job_id}',
            path: {
                'saved_job_id': savedJobId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Download Cover Letter
     * 下载求职信PDF
     * 对应Django的download_cover_letter
     * @param savedJobId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static downloadCoverLetterApiV1ApplicationsCoverLettersSavedJobIdDownloadGet(
        savedJobId: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/applications/cover-letters/{saved_job_id}/download',
            path: {
                'saved_job_id': savedJobId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Generate Custom Resume
     * 生成定制简历
     * 对应Django的generate_custom_resume_page
     * @param requestBody
     * @returns CustomResume Successful Response
     * @throws ApiError
     */
    public static generateCustomResumeApiV1ApplicationsCustomResumesPost(
        requestBody: CustomResumeCreate,
    ): CancelablePromise<CustomResume> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/applications/custom-resumes',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Custom Resume
     * 获取定制简历
     * @param userId
     * @param jobListingId
     * @returns CustomResume Successful Response
     * @throws ApiError
     */
    public static getCustomResumeApiV1ApplicationsCustomResumesUserIdJobListingIdGet(
        userId: number,
        jobListingId: string,
    ): CancelablePromise<CustomResume> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/applications/custom-resumes/{user_id}/{job_listing_id}',
            path: {
                'user_id': userId,
                'job_listing_id': jobListingId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Download Custom Resume
     * 下载定制简历PDF
     * 对应Django的download_custom_resume
     * @param userId
     * @param jobListingId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static downloadCustomResumeApiV1ApplicationsCustomResumesUserIdJobListingIdDownloadGet(
        userId: number,
        jobListingId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/applications/custom-resumes/{user_id}/{job_listing_id}/download',
            path: {
                'user_id': userId,
                'job_listing_id': jobListingId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Status Choices
     * 获取申请状态选项
     * 对应Django的SavedJob.STATUS_CHOICES
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getStatusChoicesApiV1ApplicationsStatusChoicesGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/applications/status-choices',
        });
    }
}
