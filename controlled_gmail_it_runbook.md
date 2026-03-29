# Controlled Gmail IT Runbook

## Purpose
Run the first controlled Gmail onboarding integration test with the smallest safe blast radius.

## Preconditions
- Gmail OAuth client metadata configured
- `client_secret_ref_id` present in secret storage and ACTIVE
- You have a chosen callback URL strategy
- You are ready to complete a single controlled Gmail connect attempt

## What Артём needs to provide
- Confirmation of which Gmail account to use for the first test
- Approval of the callback URL to be used
- Safe provisioning of the real Gmail OAuth client secret into backend secret storage
- A short time window to complete consent/callback without delay

## What must NOT be sent in chat
- OAuth client secret value
- Refresh token
- Raw callback URL containing sensitive parameters if avoidable

## Safe test sequence
1. Validate client secret runtime readiness
2. Start Gmail connect flow and capture:
   - mailbox_id
   - auth_session_id
   - state token
   - authorization URL
3. Open the authorization URL in a controlled browser session
4. Complete consent using the chosen Gmail test account
5. Deliver callback data into the callback service path
6. Verify:
   - mailbox state becomes ACTIVE
   - provider_account_id is persisted
   - credential ref is present
   - secret ref is ACTIVE
7. Run mailbox status and diagnostics
8. Exercise reauth on the same mailbox if needed

## Abort conditions
- callback/state mismatch
- missing or inactive `client_secret_ref_id`
- secret ref revoked unexpectedly
- unclear callback routing
- any indication that secrets may have crossed into operator-facing output

## Success criteria
- same mailbox remains the system-of-record
- Gmail callback completes successfully
- credential ref and provider account metadata persist correctly
- diagnostics remain clean and understandable
- no secret values appear in logs, chat, or status output

## After successful IT
- document exact operator steps that worked
- record provider-specific quirks
- decide whether to keep the test mailbox connected or revoke immediately
