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
| `phase1-add-tenant-id` | Add tenant_id to root entities (users, studies, packages, text_elements, audit_logs, error_logs) | **DONE** | Modified 6 model files |
| `phase1-migration-safe` | Create safe Alembic migration: create default tenant, add nullable tenant_id, backfill, set NOT NULL | **DONE** | `migrations/versions/add_multi_tenancy_foundation.py` |
| `phase1-composite-indexes` | Add composite indexes (tenant_id + status, tenant_id + created_at, etc.) | **DONE** | Included in migration |
| `phase1-tenant-context` | Create get_current_tenant_id() dependency, store tenant_id in JWT, set RLS context | **DONE** | `core/tenant.py`, updated `api/v1/auth.py` |
| `phase1-rls` | Implement PostgreSQL RLS policies; create BYPASSRLS role for super admin | **PARTIAL** | SQL in migration, needs DB testing |

**Phase 1 Commits:**
- `47e68aa` - feat: Add multi-tenancy foundation - models, schemas, CRUD, migration
- `cf7cbec` - feat: Add Stripe/SaaS config and tenant_id to JWT tokens

---

### Phase 2: Stripe Integration

| ID | Task | Status | Notes |
|----|------|--------|-------|
| `phase2-stripe-config` | Add Stripe configuration with multiple price IDs, grace period settings | **DONE** | Config added to `core/config.py` |
| `phase2-signup-flow` | Create /signup page collecting tenant name + email BEFORE Stripe Checkout | PENDING | |
| `phase2-billing-endpoints` | Create billing API with idempotent webhooks, Stripe Portal redirect | PENDING | |
| `phase2-subscription-lifecycle` | Implement grace period logic (7 days), warning emails, access restriction | PENDING | |
| `phase2-email-service` | Configure email service (SendGrid/SES) for welcome, reset, payment emails | PENDING | |

---

### Phase 3: Frontend Marketing Website

| ID | Task | Status | Notes |
|----|------|--------|-------|
| `phase3-routing` | Restructure frontend routing with session boundary handling | PENDING | |
| `phase3-landing` | Create LandingPage with SEO (meta tags, Open Graph, sitemap.xml) | PENDING | |
| `phase3-pricing` | Create PricingPage with multiple tiers, feature comparison, FAQ | PENDING | |

---

### Phase 4: Super Admin Portal

| ID | Task | Status | Notes |
|----|------|--------|-------|
| `phase4-superadmin-separate-auth` | Create /admin/login with dedicated JWT issuer, MFA enforcement | PENDING | |
| `phase4-impersonation-secure` | Implement impersonation: 1hr expiry, strict read-only, audit trail | PENDING | |
| `phase4-superadmin-frontend` | Create dashboard with ImpersonationBanner, exit mechanism, tenant list | PENDING | |

---

### Phase 5: Sample Data & Onboarding

| ID | Task | Status | Notes |
|----|------|--------|-------|
| `phase5-sample-data` | Create sample data seeding (studies, packages, text elements) | PENDING | |
| `phase5-reset-mechanism` | Add 'Reset to fresh state' endpoint to clear and re-seed tenant data | PENDING | |

---

### Phase 6: Help & Onboarding

| ID | Task | Status | Notes |
|----|------|--------|-------|
| `phase6-help-page` | Create HelpPage with video tutorials and searchable FAQ | PENDING | |
| `phase6-onboarding` | Create first-time login onboarding wizard for new tenant admins | PENDING | |

---

### Phase 7: Operational Concerns

| ID | Task | Status | Notes |
|----|------|--------|-------|
| `phase7-rate-limiting` | Implement per-tenant rate limiting and usage quotas | PENDING | |
| `phase7-gdpr-export` | Create /api/v1/tenant/export-data endpoint for GDPR compliance | PENDING | |
| `phase7-backup-restore` | Create importable backup format and import-data endpoint | PENDING | |
| `phase7-data-retention` | Implement tenant deletion policy: 90-day retention, then purge | PENDING | |

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
| Phase 1 - Foundation | 7 | 6 | 86% |
| Phase 2 - Stripe | 5 | 1 | 20% |
| Phase 3 - Marketing | 3 | 0 | 0% |
| Phase 4 - Super Admin | 3 | 0 | 0% |
| Phase 5 - Sample Data | 2 | 0 | 0% |
| Phase 6 - Help | 2 | 0 | 0% |
| Phase 7 - Operations | 4 | 0 | 0% |
| Phase 8 - Railway | 1 | 0 | 0% |
| **Total** | **27** | **7** | **26%** |

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
