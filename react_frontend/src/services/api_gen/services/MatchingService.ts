/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { MatchSession } from '../models/MatchSession';
import type { MatchSessionCreate } from '../models/MatchSessionCreate';
import type { MatchSessionResponse } from '../models/MatchSessionResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class MatchingService {
    /**
     * Debug Users
     * @returns any Successful Response
     * @throws ApiError
     */
    public static debugUsersApiV1MatchingDebugUsersGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/matching/debug/users',
        });
    }
    /**
     * Debug Profiles
     * @returns any Successful Response
     * @throws ApiError
     */
    public static debugProfilesApiV1MatchingDebugProfilesGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/matching/debug/profiles',
        });
    }
    /**
     * Debug Profile
     * @param userId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static debugProfileApiV1MatchingDebugProfileUserIdGet(
        userId: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/matching/debug/profile/{user_id}',
            path: {
                'user_id': userId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Match Session
     * 创建新的匹配会话
     * 对应Django的start_new_match_session
     * @param requestBody
     * @returns MatchSession Successful Response
     * @throws ApiError
     */
    public static createMatchSessionApiV1MatchingSessionsPost(
        requestBody: MatchSessionCreate,
    ): CancelablePromise<MatchSession> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/matching/sessions',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get User Match Sessions
     * 获取用户的匹配历史
     * 对应Django的all_matches_page
     * @param userId
     * @param skip
     * @param limit
     * @returns MatchSession Successful Response
     * @throws ApiError
     */
    public static getUserMatchSessionsApiV1MatchingSessionsGet(
        userId: number,
        skip?: number,
        limit: number = 10,
    ): CancelablePromise<Array<MatchSession>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/matching/sessions',
            query: {
                'user_id': userId,
                'skip': skip,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Match Session Detail
     * 获取特定匹配会话的详情
     * 对应Django的_handle_session_view_get
     * @param sessionId
     * @param userId
     * @returns MatchSessionResponse Successful Response
     * @throws ApiError
     */
    public static getMatchSessionDetailApiV1MatchingSessionsSessionIdGet(
        sessionId: string,
        userId?: (number | null),
    ): CancelablePromise<MatchSessionResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/matching/sessions/{session_id}',
            path: {
                'session_id': sessionId,
            },
            query: {
                'user_id': userId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Match Session
     * 删除匹配会话
     * @param sessionId
     * @param userId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteMatchSessionApiV1MatchingSessionsSessionIdDelete(
        sessionId: string,
        userId: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/matching/sessions/{session_id}',
            path: {
                'session_id': sessionId,
            },
            query: {
                'user_id': userId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
