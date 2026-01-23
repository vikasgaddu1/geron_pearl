/**
 * Zod validation schemas for Quick Start wizard forms
 */

import { z } from 'zod';

// Step 1: Study creation schema
export const studySchema = z.object({
  study_label: z
    .string()
    .min(1, 'Study label is required')
    .max(100, 'Study label must be 100 characters or less')
    .regex(/^[A-Za-z0-9_-]+$/, 'Study label can only contain letters, numbers, hyphens, and underscores'),
  description: z
    .string()
    .max(500, 'Description must be 500 characters or less')
    .optional()
    .or(z.literal('')),
});

export type StudyFormData = z.infer<typeof studySchema>;

// Step 2: Database Release schema
export const databaseReleaseSchema = z.object({
  database_release_label: z
    .string()
    .min(1, 'Release label is required')
    .max(100, 'Release label must be 100 characters or less'),
  database_release_date: z
    .string()
    .min(1, 'Release date is required'),
});

export type DatabaseReleaseFormData = z.infer<typeof databaseReleaseSchema>;

// Step 3: Package schema (optional)
export const packageSchema = z.object({
  package_name: z
    .string()
    .min(1, 'Package name is required')
    .max(100, 'Package name must be 100 characters or less'),
  study_indication: z
    .string()
    .max(200, 'Study indication must be 200 characters or less')
    .optional()
    .or(z.literal('')),
  therapeutic_area: z
    .string()
    .max(100, 'Therapeutic area must be 100 characters or less')
    .optional()
    .or(z.literal('')),
});

export type PackageFormData = z.infer<typeof packageSchema>;
