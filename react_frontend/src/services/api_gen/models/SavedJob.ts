/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { JobListing } from './JobListing';
export type SavedJob = {
    status?: string;
    notes?: (string | null);
    job_listing_id: string;
    user_id: number;
    created_at: string;
    updated_at: string;
    job_listing?: (JobListing | null);
};

