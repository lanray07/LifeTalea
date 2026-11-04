# LifeTalea receipt verifier deployment — 4 November 2026

Deployed to the owner's existing free project `guigiqacxpvcxrnajvlz`, function `lifetalea-receipts`. No plan upgrade or new paid service was added. Existing booking tables and the `routinenest-verify-receipt` function were left unchanged.

- HTTPS endpoint: `https://guigiqacxpvcxrnajvlz.supabase.co/functions/v1/lifetalea-receipts/v1/verify`
- Health: the same function prefix followed by `/health`.
- Production RVS only; fixed LifeTalea SKU and audience. Signed assertions use the separately generated RSA-3072 server identity; only its SPKI public key is tracked.
- Secrets: `LIFETALEA_AMAZON_SHARED_SECRET`, `LIFETALEA_RVS_PRIVATE_KEY_PEM_B64`, `LIFETALEA_ALLOW_AMAZON_TEST_TRANSACTIONS`. Never copy their values into Git, logs, an APK or a support message.
- The last flag is enabled for Amazon LAT. LAT/test flags remain signed in every assertion. Turn it off after testing and redeploy before public launch.
- Supabase JWT enforcement is off for this function because LifeTalea has no Supabase login. Receipt possession is verified by Amazon before a signed entitlement is returned. There is no app-embedded secret or caller-selectable upstream/environment/SKU.
- All instances consume a global database token bucket: five requests per second, burst five. `lifetalea_private.rvs_quota` stores one counter and timestamp, no customer, receipt or IP data. Its RLS denies ordinary roles; only `service_role` can call the security-invoker quota RPC. No grants were added to existing app tables.

Isolation is by namespace, not a separate security boundary: Supabase function secrets and built-in server keys are project-wide. Anyone able to deploy another function into this project could access those secrets. Restrict project administrators; use a separate project when feasible. Free quotas and project pausing can affect availability; the client must fail closed and allow retry.

Deployment verification: health returned 200/ready. Synthetic invalid identifiers were sent to the production Amazon endpoint and returned a cryptographically valid, inactive `invalid_receipt` assertion. See `amazon-supabase-deployment.json`. This is not a real purchase, refund, LAT or release-device verification.

The security advisor reports no-policy RLS on the private quota table: intentional deny-all for normal roles, with service-role-only access. Existing project warnings (including password protection) were not changed. This is not an independent security audit.

Re-deploy the files in `server/receipt-verifier/supabase/` and `src/verifier.mjs` with the same relative paths, entrypoint `supabase/index.ts`; include `supabase/deno.json`. The SQL migration is under the repository's `supabase/migrations/`. It has already been applied remotely; do not apply it a second time or reset the shared project.

Run `node --test server/receipt-verifier/test/edge.test.mjs server/receipt-verifier/test/verifier.test.mjs` before deployment. Build the separate unsigned LAT APK with `python scripts/build_amazon_test.py`. The standard release remains purchases-disabled until testing and release gates pass. Do not install the LAT app over user data without preserving the correct Amazon signing/update identity.

Supabase's [November 2026 TLS change](https://supabase.com/changelog/cbc-tls-ciphers-deprecated) removes older CBC suites. A real Fire-to-deployed-server TLS check remains required; never bypass certificate validation to make it pass.
