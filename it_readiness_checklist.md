# Gmail Controlled IT Readiness Checklist

## Goal
Safely prepare for the first controlled integration test of real Gmail onboarding.

## Must be true before IT
- [ ] OAuth client metadata exists for Gmail
- [ ] `client_secret_ref_id` exists in secret storage and is ACTIVE
- [ ] Gmail connect flow produces auth session + authorization URL
- [ ] Gmail callback path can be completed through callback service layer
- [ ] Mailbox status shows provider metadata without secret leakage
- [ ] Diagnostics explain auth/session/secret failures with remediation hints
- [ ] Reauth flow preserves the same mailbox identity

## What will still be mock/scaffold unless explicitly replaced
- Token exchange may still use a local adapter boundary instead of live Google HTTP exchange
- Callback receiver may still be simulated by direct service invocation
- Client secret storage may still be local abstraction, not production KMS

## What will be needed from Артём for real Gmail IT
- A decision on the Gmail OAuth app/client to use
- Safe provisioning path for the real client secret into backend secret storage
- Approval for the exact callback URL strategy
- A controlled window to run the first live connect attempt

## Safe handling rules
- Never send client secret or refresh token in chat
- Only pass refs / metadata through operator-facing outputs
- If callback/state mismatch appears, invalidate the session and restart cleanly
- If client secret ref is missing or revoked, stop before live auth

## Suggested pre-IT operator commands
- Validate onboarding/runtime diagnostics
- Check Gmail client secret runtime validation
- Start Gmail connect flow
- Complete via callback service path
- Verify mailbox status + diagnostics
- Exercise reauth on the same mailbox
