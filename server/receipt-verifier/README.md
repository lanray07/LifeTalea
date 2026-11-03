# LifeTalea Amazon receipt verifier

Local implementation and deployment candidate. No live Amazon receipts, hosting deployment, App Tester/DevTest/LAT purchase or production approval is claimed. Node 24 is required; there are no third-party runtime dependencies. Container execution remains unverified where Docker is unavailable.

`POST /v1/verify` accepts only `{ "userId": "Amazon SDK user ID", "receiptId": "Amazon SDK receipt ID" }`. The server fixes the Amazon host, environment and LifeTalea ENTITLED SKU. It validates Amazon's response and returns `{ "assertion": "base64url-payload.base64url-RSA-signature" }`. Invalid/canceled/user-mismatched receipts produce a signed inactive result. Upstream configuration errors, redirects, timeouts and malformed responses produce a generic 503; no URL or secret is returned.

Assertions bind the Amazon user, receipt, SKU, canonical app audience, environment and active status. They last six hours. Android verifies RSA SHA-256 with a separately pinned public key, rejects expired/mismatched assertions and sandbox assertions in release builds, and only acknowledges fulfillment after verification. The app never receives the Amazon developer shared secret or server private signing key. Local stories remain accessible when billing is unavailable.

## Run local checks

From the repository root:

```powershell
node --test server/receipt-verifier/test/verifier.test.mjs
```

Tests use fictional upstream responses, ephemeral signing keys and real local HTTP connections. The public interoperability fixture in `android/app/src/androidTest/assets/rvs-contract.json` is also verified on Fire. Its private key was discarded and its fixed timestamp is used only by tests. Never pin that test public key in a deployed app. Regenerate it deliberately, if the protocol changes, with `node server/receipt-verifier/test/export-contract-fixture.mjs` before rebuilding the test APK.

## Configure a private deployment

1. Select a host that can run a persistent Node HTTP service behind a trusted HTTPS reverse proxy. GitHub Pages cannot run this verifier or protect server secrets. No host, paid service or project was created by this implementation.
2. Generate a separate deployment signing identity outside the repository. For example: `node server/receipt-verifier/scripts/generate-signing-key.mjs C:/secure/lifetalea-sandbox.private.pem C:/secure/lifetalea-sandbox.public.b64`. Use separate identities for production and sandbox. This command refuses to overwrite existing files. Restrict private-file ACLs on Windows; POSIX file mode alone does not establish a Windows ACL.
3. Set server-only variables from `.env.example` in your host's secret manager or a protected file outside Git. Choose `RVS_ENVIRONMENT=sandbox` for App Tester, or `production` for real Amazon transactions. Set `AMAZON_SHARED_SECRET` from the developer account for production. Set exactly one of `RVS_SIGNING_PRIVATE_KEY_FILE` (a private mounted PEM) or `RVS_SIGNING_PRIVATE_KEY_PEM_B64` (base64 of that private PEM). Do not paste secrets into chat, APK properties, website configuration or CI logs.
4. Run `node --env-file=C:/secure/lifetalea-rvs.env server/receipt-verifier/src/main.mjs`. Default bind is 127.0.0.1:8080. `GET /health` exposes configuration-loaded readiness/version/environment only; it does not prove the shared secret works with Amazon. TLS must terminate outside localhost; do not expose this HTTP listener directly to the Internet.
5. For containers, build with `docker build -t lifetalea-rvs server/receipt-verifier`, mount the private PEM read-only, pass server secrets at runtime, set `HOST=0.0.0.0` inside the container, and publish the port to a private/loopback interface behind the HTTPS proxy. The Docker allowlist copies only package.json and src; no env files, keys or test material are baked in.
6. Apply deployment gateway quotas, health monitoring and secret/key rotation. The built-in quota is single-instance, up to five upstream requests/second, per-client throttling, four concurrent verifications, bounded client state and bounded payloads. It ignores untrusted forwarded-IP headers. Multiple replicas require a shared gateway quota; behind a proxy, socket-IP limiting can group clients. Load/capacity and gateway behavior require deployment testing.
7. Disable request-body logging and scrub outbound request URLs in any added proxy/APM layer: Amazon's API places its shared secret and identifiers in its request path. This service does not log receipts, tokens, account IDs or upstream URLs, stores no customer-content database, and does not accept memories/audio/photos.

Production `ALLOW_AMAZON_TEST_TRANSACTIONS=false` is the default. Amazon's production publishing/LAT transactions can have test/beta flags; enable this server-only policy deliberately for those tests. It never changes a sandbox assertion into a production assertion. Reconcile the final review/LAT policy before submission.

## Wire the Android app

Only public configuration belongs in Gradle properties:

```properties
lifetaleaRvsUrl=https://YOUR-VERIFIED-HOST/v1/verify
lifetaleaRvsPublicKey=BASE64_OF_THE_SERVER_SPKI_PUBLIC_DER_KEY
lifetaleaRvsEnvironment=production
lifetaleaPurchasesEnabled=false
```

Use `sandbox` only for debug App Tester builds; release always expects `production`. Gradle rejects a private key, non-HTTPS URL, URL credentials/query/fragment and invalid flags. The server signing public key is distinct from Amazon's existing `AppstoreAuthenticationKey.pem`. Purchases stay off by default; the switch only enables initiating a purchase and cannot bypass receipt verification. Keep it off until correct product/prices, backend TLS/secrets/key, and configured Amazon transaction tests pass. Existing entitlements can be restored with the purchase switch off.

Android restores paginated history, verifies matching receipts sequentially with time/page/count limits, rejects stale identity/request generations, and keeps signed cache only after the SDK identifies the same user. A transient verifier failure can retain an unexpired signed entitlement for a receipt still in the completed SDK history. A verified cancellation or completed empty history revokes it. Cache expires within six hours (client maximum 24 hours); expiry is checked periodically and on resume. Monotonic elapsed time anchors expiry against wall-clock changes. Persisted cache also requires the same boot counter; after reboot, or if the OS cannot provide that counter, fresh verification is required. Without successful SDK identity resolution at launch, Premium is unavailable rather than trusting a cached boolean; ordinary local content remains available. Account identity/offline behavior and Amazon lifecycle races still require real App Tester/LAT testing.

Preserve the deployment signing identity securely. The current protocol pins one public signing key per build; signing-key rotation requires a coordinated app update, not an automatic multi-key rollover. Rotating Amazon's separate shared secret is server-only and does not require changing the app's signing-key pin.

## Account and release work still required

Create/approve the missing `com.lifetalea.premium` ENTITLED product and marketplace prices, install/configure App Tester or the relevant Amazon test channel, deploy the verifier with real credentials and trusted HTTPS, pin its public key, then test purchase, pending/failure, restore, refund, account switching, interruptions and offline recovery. No production credential or persistent deployment signing key was generated during local tests.

Official references: [Amazon RVS contract](https://developer.amazon.com/docs/in-app-purchasing/iap-rvs-for-android-apps.html), [SDK integration and package visibility](https://developer.amazon.com/docs/in-app-purchasing/iap-implement-iap.html), [RVS sandbox](https://www.developer.amazon.com/docs/in-app-purchasing/rvs-cloud-sandbox.html). The service implements one-time ENTITLED purchases; subscriptions/consumables are intentionally rejected.
