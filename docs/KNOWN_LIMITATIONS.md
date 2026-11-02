# Known limitations and remaining engineering

This is a development build. Release readiness is BLOCKED independently of whether a source component compiles.

- Automatic recorded-file transcription has an unavailable adapter only. It needs a real engine, consent/status/retry workflow and tested languages.
- App source strings are English. Translation APIs are not configured, native approval is absent, website/store translation generation needs completion, and worldwide screenshots are missing.
- English voice command parsing exists; other dictionaries are pending. Recognition/TTS capabilities depend on installed services and require locale-specific tests. Audio seek, focus interruptions, permission denial and long recordings need broader tests.
- Amazon purchasing cannot be validated until the correct authentication PEM, entitlement product and test setup are supplied. A production server receipt-verification service is not implemented. No real payment was taken.
- Current backup uses bounded in-memory archives: 32 MiB total, 16 MiB per item, with conservative creation reserve. Large photos or long recordings may exceed the cap. Streaming export/restore, crash journalling and fuzz/low-memory tests remain necessary.
- Scrapbooks use simple story/photo page arrangements and one editable caption per page. There is no freeform drag canvas. PDF exports use the first photograph per selected memory; multi-photo printable layouts, contents pages and richer cover typography remain enhancements. PDF preview uses scrapbook preview rather than an embedded PDF viewer.
- The onboarding purpose selection is presentation-only; it does not yet personalise future prompts. Reminders, optional app lock, advanced search controls, premium theme differentiation and a larger prompt catalogue are incomplete. Current search includes title/story/tags/transcript/location/date and an album filter.
- A duplicated entry currently duplicates its written fields and album associations; it does not copy attachment binaries. User-owned original attachments remain intact.
- There is one Gradle application with package boundaries, not a full independent-module Clean Architecture graph. No previous database release exists, so future migrations still require new test fixtures and explicit migration code.
- Only one physical Fire device is available in this session. Other Fire/phone sizes, landscape, accessibility services, large font settings, performance budgets and prolonged offline use need a complete device matrix. No Fire TV UI exists.
- The marketing site is a local static preview. GitHub source/policy/support URLs are provided; no production website or store listing is published. Final locale availability, country selection, signing/update identity, native-language review, privacy/legal review, asset polish and name clearance remain required.

These limitations are included to keep source delivery, implemented behaviour and release approval distinct. They must not be omitted from a public launch decision.
