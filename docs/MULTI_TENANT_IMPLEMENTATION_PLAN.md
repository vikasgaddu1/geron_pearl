# Multi-Tenant SaaS Transformation - Implementation Plan

This document tracks the implementation progress for transforming PEARL into a multi-tenant SaaS platform.

**Related Documents:**
- [Plan Review & Feedback](./MULTI_TENANT_PLAN_REVIEW.md) - Original concerns and solutions

---

## Implementation Checklist

### Phase 1: Database Multi-Tenancy Foundation

| ID | Task | Status | Notes |
|----|------|--------|-------|
| `phase1-tenant-model` | Create Tenant model with soft-delete, TenantSettings model, SubscriptionPlan table | **DONE** | `models/tenant.py`, `models/subscription_plan.py`, `models/tenant_settings.py` |
| `phase1-superadmin-table` | Create separate SuperAdmin table with MFA fields and separate JWT issuer | **DONE** | `models/super_admin.py` |
| `phase1-add-tenant-id` | Add tenant_id to root entities (users, studies, packages, text_elements, audit_logs, error_logs, notifications, app_settings) | **DONE** | Modified 8 model files |
| `phase1-migration-safe` | Create safe Alembic migration: create default tenant, add nullable tenant_id, backfill, set NOT NULL | **DONE** | `migrations/versions/add_multi_tenancy_foundation.py` |
| `phase1-composite-indexes` | Add composite indexes (tenant_id + status, tenant_id + created_at, etc.) | **DONE** | Included in migration |
| `phase1-tenant-context` | Create get_current_tenant_id() dependency, store tenant_id in JWT, set RLS context | **DONE** | `core/tenant.py`, updated `api/v1/auth.py`, registered in `main.py` |
| `phase1-rls` | Implement PostgreSQL RLS policies; create BYPASSRLS role for super admin | **DONE** | `migrations/versions/add_rls_policies.py` |

**Phase 1 Commits:**
- `47e68aa` - feat: Add multi-tenancy foundation - models, schemas, CRUD, migration
- `cf7cbec` - feat: Add Stripe/SaaS config and tenant_id to JWT tokens

**Phase 1 Bug Fixes (from phase1_issues.md review):**
- Added RLS policies migration with `ENABLE ROW LEVEL SECURITY`, `FORCE ROW LEVEL SECURITY`, and `CREATE POLICY`
- Created `pearl_super_admin` role with `BYPASSRLS` privilege
- Added `tenant_id` to `notifications` and `app_settings` models
- Fixed username uniqueness: now per-tenant (`UniqueConstraint('tenant_id', 'username')`) instead of global
- Registered `TenantContextMiddleware` in `main.py`
- Fixed Boolean/Integer type mismatch in `tenant_settings.py` and `subscription_plan.py`
- Assigned default plan to default tenant in migration

---

### Phase 2: Stripe Integration

| ID | Task | Status | Notes |
|----|------|--------|-------|
| `phase2-stripe-config` | Add Stripe configuration with multiple price IDs, grace period settings | **DONE** | Config added to `core/config.py` |
| `phase2-signup-flow` | Create /signup page collecting tenant name + email BEFORE Stripe Checkout | **DONE** | Backend: `api/v1/billing.py` - `/signup/initiate` endpoint |
| `phase2-billing-endpoints` | Create billing API with idempotent webhooks, Stripe Portal redirect | **DONE** | `api/v1/billing.py` - webhooks, portal, overview |
| `phase2-subscription-lifecycle` | Implement grace period logic (7 days), warning emails, access restriction | **DONE** | `core/subscription.py` - access middleware |
| `phase2-email-service` | Configure email service (SendGrid/SES) for welcome, reset, payment emails | **DONE** | Added billing emails to `core/email.py` |

**Phase 2 Files Created:**
- `backend/app/api/v1/billing.py` - Billing API endpoints
- `backend/app/core/stripe.py` - Stripe service functions
- `backend/app/core/subscription.py` - Subscription access middleware
- `backend/app/schemas/billing.py` - Billing schemas

---

### Phase 3: Frontend Marketing Website

| ID | Task | Status | Notes |
|----|------|--------|-------|
| `phase3-routing` | Restructure frontend routing with session boundary handling | **DONE** | `/` = public, `/app/*` = protected |
| `phase3-landing` | Create LandingPage with SEO (meta tags, Open Graph, sitemap.xml) | **DONE** | Hero, features, testimonials, CTA |
| `phase3-pricing` | Create PricingPage with multiple tiers, feature comparison, FAQ | **DONE** | Dynamic plans from API, comparison table |
| `phase3-signup` | Create SignupPage that integrates with Stripe | **DONE** | Form validation, Stripe redirect |

**Phase 3 Files Created:**
- `react-frontend/src/features/marketing/LandingPage.tsx` - Marketing homepage
- `react-frontend/src/features/marketing/PricingPage.tsx` - Pricing with plans
- `react-frontend/src/features/marketing/SignupPage.tsx` - Signup form
- `react-frontend/src/api/endpoints/billing.ts` - Billing API client

---

### Phase 4: Super Admin Portal

| ID | Task | Status | Notes |
|----|------|--------|-------|
| `phase4-superadmin-separate-auth` | Create /admin/login with dedicated JWT issuer, MFA enforcement | **DONE** | `core/super_admin_security.py` |
| `phase4-impersonation-secure` | Implement impersonation: 1hr expiry, strict read-only, audit trail | **DONE** | Audit logged to audit_log table |
| `phase4-superadmin-frontend` | Create dashboard with ImpersonationBanner, exit mechanism, tenant list | **DONE** | `features/super-admin/` |

**Phase 4 Backend Files:**
- `backend/app/core/super_admin_security.py` - JWT, MFA, impersonation tokens
- `backend/app/crud/super_admin.py` - CRUD operations
- `backend/app/schemas/super_admin.py` - Pydantic schemas
- `backend/app/api/v1/super_admin.py` - API endpoints

**Phase 4 Frontend Files:**
- `react-frontend/src/features/super-admin/SuperAdminLoginPage.tsx`
- `react-frontend/src/features/super-admin/SuperAdminDashboard.tsx`
- `react-frontend/src/components/layout/ImpersonationBanner.tsx`
- `react-frontend/src/api/endpoints/super-admin.ts`

---

### Phase 5: Sample Data & Onboarding

| ID | Task | Status | Notes |
|----|------|--------|-------|
| `phase5-sample-data` | Create sample data seeding (studies, packages, text elements) | **DONE** | `services/sample_data.py` |
| `phase5-reset-mechanism` | Add 'Reset to fresh state' endpoint to clear and re-seed tenant data | **DONE** | `/api/v1/tenant/*` endpoints |

**Phase 5 Files Created:**
- `backend/app/services/sample_data.py` - Sample data definitions and seeding functions
- `backend/app/api/v1/tenant_data.py` - Tenant data management endpoints
- `backend/migrations/versions/add_tenant_onboarding_fields.py` - Migration for tenant flags
- `react-frontend/src/api/endpoints/tenant-data.ts` - Frontend API client

---

### Phase 6: Help & Onboarding

| ID | Task | Status | Notes |
|----|------|--------|-------|
| `phase6-help-page` | Create HelpPage with video tutorials and searchable FAQ | **DONE** | `HelpPage.tsx` with FAQ and tutorials |
| `phase6-onboarding` | Create first-time login onboarding wizard for new tenant admins | **DONE** | `OnboardingWizard.tsx` with multi-step tour |

**Phase 6 Files Created:**
- `react-frontend/src/features/help/HelpPage.tsx` - Searchable FAQ, video tutorials, help center
- `react-frontend/src/features/onboarding/OnboardingWizard.tsx` - Multi-step onboarding for new admins
- `react-frontend/src/features/onboarding/OnboardingProvider.tsx` - Context provider for onboarding
- `react-frontend/src/features/settings/SampleDataSettings.tsx` - UI for sample data management
- `react-frontend/src/hooks/useOnboarding.ts` - Onboarding state management hook
- `backend/app/api/v1/tenant_data.py` - Added onboarding status/complete endpoints

---

### Phase 7: Operational Concerns

| ID | Task | Status | Notes |
|----|------|--------|-------|
| `phase7-rate-limiting` | Implement per-tenant rate limiting and usage quotas | **DONE** | `core/rate_limiting.py` with sliding window |
| `phase7-gdpr-export` | Create /api/v1/tenant/export-data endpoint for GDPR compliance | **DONE** | JSON and ZIP export options |
| `phase7-backup-restore` | Create importable backup format and import-data endpoint | **DONE** | Backup/restore with validation |
| `phase7-data-retention` | Implement tenant deletion policy: 90-day retention, then purge | **DONE** | Soft delete with 90-day retention |

**Phase 7 Files Created:**
- `backend/app/core/rate_limiting.py` - Per-tenant rate limiting with sliding window algorithm
- `backend/app/services/data_export.py` - GDPR-compliant data export (JSON/ZIP)
- `backend/app/services/backup_restore.py` - Backup creation and restoration
- `backend/app/services/data_retention.py` - Soft delete and data retention policies
- `backend/app/api/v1/tenant_data.py` - Added export, backup, restore, usage endpoints

---

### Phase 8: Railway Deployment

| ID | Task | Status | Notes |
|----|------|--------|-------|
| `phase8-railway-setup` | Configure Railway: cron service with health endpoint, cost alerts | PENDING | |

---

## File Ownership by Phase

To minimize merge conflicts during parallel development:

| Phase | Backend Files | Frontend Files |
|-------|--------------|----------------|
| **Phase 1** (Foundation) | `models/tenant.py`, `models/super_admin.py`, `models/subscription_plan.py`, `models/tenant_settings.py`, `crud/tenant.py`, `crud/super_admin.py`, `core/tenant.py`, `migrations/*tenant*` | - |
| **Phase 2** (Stripe) | `api/v1/billing.py`, `api/v1/signup.py`, `core/stripe.py`, `tasks/billing.py`, `schemas/billing.py` | `api/endpoints/billing.ts`, `features/signup/` |
| **Phase 3** (Marketing) | - | `features/marketing/LandingPage.tsx`, `features/marketing/PricingPage.tsx`, `components/SEO.tsx` |
| **Phase 4** (Super Admin) | `api/v1/super_admin.py`, `core/super_admin_security.py` | `features/super-admin/*`, `components/ImpersonationBanner.tsx` |
| **Phase 5-6** (Sample/Help) | `db/sample_data.py` | `features/help/`, `features/onboarding/` |
| **Phase 7-8** (Ops) | `tasks/cleanup.py`, `cron_worker.py` | - |

---

## Progress Summary

| Phase | Total Tasks | Completed | Progress |
|-------|-------------|-----------|----------|
| Phase 1 - Foundation | 7 | 7 | 100% |
| Phase 2 - Stripe | 5 | 5 | 100% |
| Phase 3 - Marketing | 4 | 4 | 100% |
| Phase 4 - Super Admin | 3 | 3 | 100% |
| Phase 5 - Sample Data | 2 | 2 | 100% |
| Phase 6 - Help | 2 | 2 | 100% |
| Phase 7 - Operations | 4 | 4 | 100% |
| Phase 8 - Railway | 1 | 0 | 0% |
| **Total** | **28** | **27** | **96%** |

---

## Next Steps

1. **Test Migration**: Run `alembic upgrade head` against a test database to verify the migration works
2. **Phase 2**: Implement Stripe billing endpoints and webhook handler
3. **Phase 3**: Create marketing landing page (can be done in parallel)

---

## Architecture Reference

```
Public Pages (/)           Tenant App (/app)           Super Admin (/admin)
─────────────────          ──────────────────          ────────────────────
Landing Page               Login                       Admin Login + MFA
Pricing Page               Onboarding Wizard           Tenant Management
Signup → Stripe            Dashboard                   Impersonation (read-only)
Help Page                  All Features                SaaS Analytics
```

**Database Isolation**: PostgreSQL Row-Level Security (RLS) with `SET LOCAL app.current_tenant_id`

**Super Admin Bypass**: Uses `BYPASSRLS` database role, NOT policy conditions
