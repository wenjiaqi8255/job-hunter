/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_upload_cv_file_api_v1_profiles__user_id__upload_cv_post } from '../models/Body_upload_cv_file_api_v1_profiles__user_id__upload_cv_post';
import type { UserProfile } from '../models/UserProfile';
import type { UserProfileCreate } from '../models/UserProfileCreate';
import type { UserProfileUpdate } from '../models/UserProfileUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ProfilesService {
    /**
     * Get User Profile
     * 获取用户个人资料
     * 对应Django的profile_page GET请求
     * @param userId
     * @returns UserProfile Successful Response
     * @throws ApiError
     */
    public static getUserProfileApiV1ProfilesUserIdGet(
        userId: number,
    ): CancelablePromise<UserProfile> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/profiles/{user_id}',
            path: {
                'user_id': userId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update User Profile
     * 更新用户个人资料
     * 对应Django的profile_page POST请求
     * @param userId
     * @param requestBody
     * @returns UserProfile Successful Response
     * @throws ApiError
     */
    public static updateUserProfileApiV1ProfilesUserIdPut(
        userId: number,
        requestBody: UserProfileUpdate,
    ): CancelablePromise<UserProfile> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/profiles/{user_id}',
            path: {
                'user_id': userId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete User Profile
     * 删除用户个人资料
     * @param userId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteUserProfileApiV1ProfilesUserIdDelete(
        userId: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/profiles/{user_id}',
            path: {
                'user_id': userId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create User Profile
     * 创建用户个人资料
     * @param requestBody
     * @returns UserProfile Successful Response
     * @throws ApiError
     */
    public static createUserProfileApiV1ProfilesPost(
        requestBody: UserProfileCreate,
    ): CancelablePromise<UserProfile> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/profiles/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Upload Cv File
     * 上传简历文件
     * 对应Django的CV文件上传逻辑
     * @param userId
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static uploadCvFileApiV1ProfilesUserIdUploadCvPost(
        userId: number,
        formData: Body_upload_cv_file_api_v1_profiles__user_id__upload_cv_post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/profiles/{user_id}/upload-cv',
            path: {
                'user_id': userId,
            },
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Improvement Tips
     * 获取个人资料改进建议
     * 对应Django的tips_to_improve_page
     * @param userId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getImprovementTipsApiV1ProfilesUserIdTipsGet(
        userId: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/profiles/{user_id}/tips',
            path: {
                'user_id': userId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
