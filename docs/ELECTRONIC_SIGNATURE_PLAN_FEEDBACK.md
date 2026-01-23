# Electronic Signature Plan - Critical Review & Gaps

This document provides a critical analysis of [ELECTRONIC_SIGNATURE_PLAN.md](./ELECTRONIC_SIGNATURE_PLAN.md) identifying gaps and areas that need clarification before implementation.

---

## 1. Security Gaps

### TOTP Secret Storage
- The plan stores `signature_secret` as plaintext `String(255)`. TOTP secrets should be **encrypted at rest** using the application's encryption key, not stored in plaintext.

### No Rate Limiting
- Missing: Rate limiting on TOTP verification endpoints. Without this, brute-force attacks on the 6-digit code (1 million combinations) are feasible. Should add lockout after 3-5 failed attempts.

### No Backup/Recovery Mechanism
- What happens if a user loses their phone/authenticator? No mention of:
  - Backup codes (like super admin MFA has)
  - Admin-assisted TOTP reset procedure
  - Re-enrollment flow after device loss

### No Secret Revocation
- No endpoint to revoke/regenerate TOTP secret if compromised. Users should be able to reset their signature authentication.

---

## 2. Regulatory Compliance Gaps (21 CFR Part 11 / EU Annex 11)

### Missing Signature Intent/Meaning
- Regulatory-grade signatures require the signer to acknowledge the **meaning** of the signature. The plan has a "reason" field but doesn't enforce selecting a purpose like:
  - "I approve this submission"
  - "I certify this is accurate and complete"
  - "I authorize release to production"

### "No Void Option" is Problematic
- 21 CFR Part 11 §11.10(e) requires ability to correct errors with audit trail. A signed document with errors needs a correction mechanism. Consider:
  - Add a "supersede" action that creates a new RE version
  - Or allow "void with justification" that preserves full audit trail

### Single Signature May Be Insufficient
- Many regulatory contexts require **dual signatures** (author + reviewer, or QC + QA). The plan explicitly states "single signature" but should at least document when dual signatures would be needed.

### Trusted Timestamping
- `signed_at` appears to use server time. For regulatory purposes, consider documenting that this is server-authoritative (not client-provided) and potentially adding timezone info.

---

## 3. Functional Gaps

### Post-Signature Data Integrity
- What prevents modification/deletion of items after signing? The plan should specify:
  - Signed REs cannot have items added/deleted
  - Underlying packages/text elements cannot be deleted if referenced by signed REs
  - User who signed cannot be deleted (or at least their signature data is preserved)

### No Signature Verification Endpoint
- Missing: `GET /{id}/verify-signature` to cryptographically verify a signature hash against current items snapshot. This is essential for auditors to validate integrity.

### No WebSocket Broadcast
- The plan doesn't mention broadcasting signature events. Should add:
  - `reporting_effort_signed` WebSocket message
  - Notify study members when an RE is signed

### No Export/Print with Signature
- How does the signature appear when RE data is exported or printed? Should include:
  - Signer name, timestamp, reason
  - Hash for verification
  - QR code linking to verification?

### Missing Notifications
- No mention of notifying stakeholders (study LEADs, admins) when an RE is signed.

---

## 4. Edge Cases Not Addressed

| Scenario | Gap |
|----------|-----|
| Items change between readiness check and sign | Need transactional lock or optimistic concurrency check |
| Already-locked RE is signed | Document behavior: should signing fail if locked by someone else? |
| User signs then is deactivated | Preserve signature data when user is deleted/deactivated |
| Study deletion | Prevent deletion of studies containing signed REs |
| Clock drift | TOTP has 30-second windows; document acceptable drift |
| Concurrent sign attempts | Two users attempting to sign simultaneously - who wins? |

---

## 5. Authorization Ambiguity

### "Responsible User" Undefined
- Plan states "Admin users OR responsible users for the study" but doesn't define "responsible". Based on PEARL's role system, this should explicitly state:
  - `is_admin = True` users, OR
  - Users with `LEAD` role for the study

### Frontend Integration
- The frontend already has `authStore.isResponsibleForStudy()` helper - the plan should reference it for consistency.

---

## 6. Implementation Gaps

### Missing Schema Details
- `ReportingEffortSignatureHistory` model (line 42-45) is incomplete. Needs:
  - `id` (primary key)
  - Timestamps (`created_at`)
  - All field types specified

### Missing Model Relationships
- Need to define SQLAlchemy relationships:
  - `ReportingEffort.signature_history` (one-to-many)
  - `ReportingEffort.signed_by` (relationship to User)
  - `ReportingEffortSignatureHistory.signed_by` (relationship to User)

### Validation Rules Missing
- Should `signature_reason` be required? Minimum length?
- Should there be a pre-defined list of signing reasons?

### Lock Interaction Not Clear
- Plan says "auto-lock" but:
  - What if RE is already locked by someone else?
  - Does signing set `lock_reason` to "Signed"?
  - Can a signed RE ever be unlocked? (Answer should be NO)

---

## 7. UX Gaps

### List View Status
- No mention of showing signature status (badge, icon) in RE list views

### Filter/Search
- No mention of filtering by signed/unsigned status

### Setup Prompt
- No guided flow prompting users to set up signature TOTP when they first try to sign

### Error Feedback
- What happens when:
  - TOTP code is wrong?
  - Not all items in production?
  - User doesn't have TOTP setup?

---

## 8. Testing Gaps

### Test Script Scope
- `test_electronic_signature.sh` mentioned but no test cases listed:
  - Happy path signing
  - Signing without TOTP setup (should fail)
  - Signing with items not in production (should fail)
  - TOTP rate limiting
  - Signature verification
  - Concurrent signing attempts

---

## Recommended Additions

| # | Recommendation | Priority |
|---|----------------|----------|
| 1 | Add TOTP secret encryption using `cryptography.fernet` | High |
| 2 | Add rate limiting: 5 failed TOTP attempts = 15-minute lockout | High |
| 3 | Add backup codes: Generate 10 one-time codes during setup (like super admin MFA) | High |
| 4 | Add signature verification endpoint: `GET /{id}/verify-signature` | High |
| 5 | Add void/supersede mechanism with full audit trail | Medium |
| 6 | Define "responsible user" explicitly as admin OR study LEAD | High |
| 7 | Add WebSocket broadcast for signature events | Medium |
| 8 | Prevent unlock after signing: Add `is_signed` check to unlock endpoint | High |
| 9 | Add deletion protection: Studies/REs/Users involved in signatures cannot be deleted | High |
| 10 | Document clock tolerance: Typically ±1 time step (30 seconds) for TOTP | Low |

---

## Summary

The plan provides a solid foundation but needs refinement in these key areas before implementation:

1. **Security hardening** - Encrypt secrets, add rate limiting, provide recovery mechanism
2. **Regulatory completeness** - Signature intent, void mechanism, verification endpoint
3. **Data integrity** - Post-signature protection, deletion prevention
4. **Authorization clarity** - Explicitly define who can sign
5. **Lock integration** - Prevent unlock after signing, handle lock conflicts

Address these gaps to ensure the electronic signature feature meets regulatory requirements and provides robust audit trail capabilities.
