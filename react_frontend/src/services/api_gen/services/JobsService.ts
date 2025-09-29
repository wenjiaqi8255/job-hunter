/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { JobListing } from '../models/JobListing';
import type { JobListingCreate } from '../models/JobListingCreate';
import type { JobListingUpdate } from '../models/JobListingUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class JobsService {
    /**
     * Get All Jobs
     * 获取所有工作职位列表
     * 对应Django main_views中的all_jobs_annotated逻辑
     * @param skip
     * @param limit
     * @param industry
     * @param location
     * @returns JobListing Successful Response
     * @throws ApiError
     */
    public static getAllJobsApiV1JobsGet(
        skip?: number,
        limit: number = 100,
        industry?: (string | null),
        location?: (string | null),
    ): CancelablePromise<Array<JobListing>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/jobs/',
            query: {
                'skip': skip,
                'limit': limit,
                'industry': industry,
                'location': location,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Job
     * 创建新工作职位
     * 对应Django中_save_job_matches_to_db的逻辑
     * @param requestBody
     * @returns JobListing Successful Response
     * @throws ApiError
     */
    public static createJobApiV1JobsPost(
        requestBody: JobListingCreate,
    ): CancelablePromise<JobListing> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/jobs/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Job Detail
     * 获取工作详情
     * 对应Django的job_detail_page
     * @param jobId
     * @returns JobListing Successful Response
     * @throws ApiError
     */
    public static getJobDetailApiV1JobsJobIdGet(
        jobId: string,
    ): CancelablePromise<JobListing> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/jobs/{job_id}',
            path: {
                'job_id': jobId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Job
     * 更新工作职位信息
     * @param jobId
     * @param requestBody
     * @returns JobListing Successful Response
     * @throws ApiError
     */
    public static updateJobApiV1JobsJobIdPut(
        jobId: string,
        requestBody: JobListingUpdate,
    ): CancelablePromise<JobListing> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/jobs/{job_id}',
            path: {
                'job_id': jobId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Job
     * 删除工作职位
     * @param jobId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteJobApiV1JobsJobIdDelete(
        jobId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/jobs/{job_id}',
            path: {
                'job_id': jobId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Industries
     * 获取所有行业列表
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getIndustriesApiV1JobsSearchIndustriesGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/jobs/search/industries',
        });
    }
    /**
     * Get Locations
     * 获取所有地区列表
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getLocationsApiV1JobsSearchLocationsGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/jobs/search/locations',
        });
    }
}
