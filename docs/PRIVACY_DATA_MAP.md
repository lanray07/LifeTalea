# Privacy implementation review — 10 November 2026

This is a technical data map for candidate version 5, not a legal approval or a submitted store questionnaire.

| Data / action | Destination and purpose | Retention / deletion |
| --- | --- | --- |
| Stories, dates, tags, manually entered locations, transcripts, photos and recordings | Private Android app storage; no automatic content upload | Local library controls remove records/files; uninstall removes private app data. Separately exported copies require separate deletion. |
| Saved-file transcription | Bundled model and native engine on device; user confirms processing and reviews the draft | Original audio retained; generated draft is saved only on explicit append. No transcription-provider endpoint. |
| Push-to-talk commands / spoken playback | Installed Android recognition or TTS service, which can use its provider's network services | Provider-dependent; contextual disclosure and text/touch alternatives are present. Do not describe all speech processing as offline. |
| Amazon app-specific user ID and receipt ID | HTTPS to LifeTalea's Supabase-hosted verifier, then Amazon RVS, for entitlement verification | Handler does not intentionally log bodies or credentials. Platform invocation/access logs can include identifiers and connection metadata. Actual retention and processing region still need publisher assessment. |
| Signed entitlement assertion | Private app storage; binds user, receipt, SKU and expiry | Cached assertion is replaced/refreshed; local deletion is separate from Amazon transaction retention. |
| Shared rate-limit counter and timestamp | Dedicated Supabase quota table; abuse/cost control | No customer, receipt or IP identifier columns in this application table. This does not imply platform logs contain no identifiers. |
| PDF / backup exports | User-selected Android document provider; may be a cloud destination | User controls exported copies and passphrases. Unencrypted archives are readable. Archive encryption does not encrypt the local database. |
| Reminder preference, alarm and generic notification | Local preferences and Android notification/alarm service; optional daily prompt | Off by default; disabling cancels the app's alarm and notification. No library content is read for the notification and no delivery telemetry is added. |
| Support correspondence | Publisher's support mailbox when the user chooses to contact support | Avoid collecting stories, recordings, backups or passwords; mailbox handling and final retention policy require publisher review. |

Source evidence: `SettingsScreen.kt`, `StoryReminders.kt`, `RecordedAudio.kt`, `OfflineTranscription.kt`, `ReceiptVerification.kt`, `server/receipt-verifier/supabase/handler.mjs`, `index.ts`, and the quota migration. The application has no advertising or analytics SDK dependency. Narrow static checks are not an independent security audit.

The store disclosure must account for purchase identifiers and provider logging, even though journal content remains local. Do not answer that the entire application has no network processing. The currently published policy URL points to the repository's `PRIVACY_POLICY.md`.

Remaining publisher checks: actual hosted logging/retention and processing region; provider contracts and international-transfer assessment; final store question wording and declarations; age/audience and rights requests. No consent to purchase, export compliance certification or legal declaration was made on the publisher's behalf in this pass.

Provider references checked: [Supabase logging](https://supabase.com/docs/guides/functions/logging), [Android inexact alarms](https://developer.android.com/develop/background-work/services/alarms), [Android notification permission](https://developer.android.com/develop/ui/compose/notifications/notification-permission). The Supabase changelog Markdown endpoint could not be rendered by the web tool; no Supabase API or deployment was changed.
