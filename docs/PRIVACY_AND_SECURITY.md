# Privacy and security implementation

See PRIVACY_POLICY.md for user-facing disclosures. Current protections include private app media, contextual microphone permission, Storage Access Framework export, no location permission, disabled system backup, no ad/analytics SDKs, no mandatory account, no app-owned cloud upload endpoints and no production secrets in source by design.

Backup input is bounded and checked before import. Imported paths cannot traverse directories. Attachment hashes are verified. Encrypted archives use authenticated encryption; wrong passwords and tampering must fail before mutation. Deletion removes database records and associated media. Database and media storage depend on device protections; separate database encryption and optional app lock are not implemented.

Remaining security review: backup fuzzing and memory-pressure testing, filesystem/database crash consistency, dependency review, exported component review with the final Amazon key/SDK settings, production receipt validation, physical permission-denial/interruption tests, legal assessment and device accessibility review. No independent security audit or GDPR certification is claimed.

The verified app-specific Amazon authentication PEM is a public RSA key intentionally bundled in assets (AMAZON_PUBLIC_KEY.md). It is not a developer shared secret or private signing key. The Appstore SDK can initialise licensing/account refresh on app launch; the development privacy notice now states this. Server receipt verification remains unimplemented and production purchasing fails closed. A formal Security Scan startup attempt failed on 3 November; no independent audit was completed.
