/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { JobListing } from './JobListing';
/**
 * 工作匹配响应
 */
export type JobMatchResponse = {
    job_object: JobListing;
    reason?: (string | null);
    score: number;
    tips?: (string | null);
    parsed_tips_list?: Array<string>;
    parsed_insights_list?: Array<string>;
    job_anomalies?: Array<Record<string, any>>;
    saved_status?: (string | null);
};

