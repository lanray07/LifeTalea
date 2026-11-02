# Privacy and security implementation

See PRIVACY_POLICY.md for user-facing disclosures. Current protections include private app media, contextual microphone permission, Storage Access Framework export, no location permission, disabled system backup, no ad/analytics SDKs, no mandatory account, no app-owned cloud upload endpoints and no production secrets in source by design.

Backup input is bounded and checked before import. Imported paths cannot traverse directories. Attachment hashes are verified. Encrypted archives use authenticated encryption; wrong passwords and tampering must fail before mutation. Deletion removes database records and associated media. Database and media storage depend on device protections; separate database encryption and optional app lock are not implemented.

Remaining security review: backup fuzzing and memory-pressure testing, filesystem/database crash consistency, dependency review, exported component review with the final Amazon key/SDK settings, production receipt validation, physical permission-denial/interruption tests, legal assessment and device accessibility review. No independent security audit or GDPR certification is claimed.
