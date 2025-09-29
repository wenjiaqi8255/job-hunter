/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DataSyncService {
    /**
     * Get Sync Status
     * 获取数据同步状态
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getSyncStatusApiV1SyncSyncStatusGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sync/sync/status',
        });
    }
    /**
     * Validate Data Consistency
     * 验证数据一致性
     * @returns any Successful Response
     * @throws ApiError
     */
    public static validateDataConsistencyApiV1SyncSyncValidatePost(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/sync/sync/validate',
        });
    }
    /**
     * Repair Data Issues
     * 修复数据问题
     * @returns any Successful Response
     * @throws ApiError
     */
    public static repairDataIssuesApiV1SyncSyncRepairPost(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/sync/sync/repair',
        });
    }
    /**
     * Get Table Structure
     * 获取数据库表结构
     * @param tableName
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getTableStructureApiV1SyncSyncTablesStructureTableNameGet(
        tableName: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sync/sync/tables/structure/{table_name}',
            path: {
                'table_name': tableName,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Test Database Connection
     * 测试数据库连接
     * @returns any Successful Response
     * @throws ApiError
     */
    public static testDatabaseConnectionApiV1SyncSyncTestConnectionPost(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/sync/sync/test-connection',
        });
    }
}
