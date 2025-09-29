/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { JobMatchResponse } from './JobMatchResponse';
import type { MatchSession } from './MatchSession';
/**
 * 匹配会话响应
 */
export type MatchSessionResponse = {
    session: MatchSession;
    matched_jobs: Array<JobMatchResponse>;
    total_matches: number;
};

