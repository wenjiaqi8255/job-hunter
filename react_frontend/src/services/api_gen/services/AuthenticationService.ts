/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LoginRequest } from '../models/LoginRequest';
import type { User } from '../models/User';
import type { UserCreate } from '../models/UserCreate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AuthenticationService {
    /**
     * Register User
     * 用户注册
     * 对应Django的register_view
     * @param requestBody
     * @returns User Successful Response
     * @throws ApiError
     */
    public static registerUserApiV1AuthRegisterPost(
        requestBody: UserCreate,
    ): CancelablePromise<User> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/auth/register',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Login
     * 用户登录
     * 对应Django的login视图
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static loginApiV1AuthLoginPost(
        requestBody: LoginRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/auth/login',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Current User
     * 获取当前用户信息
     * 对应Django的get_current_user_info
     * @param userId
     * @returns User Successful Response
     * @throws ApiError
     */
    public static getCurrentUserApiV1AuthMeGet(
        userId?: (number | null),
    ): CancelablePromise<User> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/auth/me',
            query: {
                'user_id': userId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Logout
     * 用户登出
     * 对应Django的logout视图
     * @returns any Successful Response
     * @throws ApiError
     */
    public static logoutApiV1AuthLogoutPost(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/auth/logout',
        });
    }
}
