# Amazon version 5 LAT review — 10 November 2026

Version 5 is live on **Test 1** as **LifeTalea v5 product and privacy verification**. Amazon shows **Test in-progress** for release `amzn1.devportal.apprelease.4d97054e1cd6403581311e1ca8b018e3`. The exact uploaded APK has SHA-256 `6d0f548a91642de13d92a58e5e59de9b5ac61a950d6795187381fabc493ed582`. Amazon parsed version code 5, applied DRM and retained 12 selected Fire tablets, English language support and the existing owner's export certification. No new legal declaration or tester/account change was made.

The console's public SHA-256 signing-certificate identity is `8e35b165d5a1dc14c10820cee25ed2c24e9c543ceb2f059b9f5bc93baa672297`, matching the earlier Amazon-installed build. This is console metadata, not inspection of an installed version 5 APK.

**Tablet verification is waiting for the owner to unlock its PIN screen.** USB debugging is authorized, but the regular Amazon package still reports version code 4 and installer `com.amazon.venezia`. No version 5 install, launch, filters, reminder, transcription or billing outcome is claimed. The unlock request is pending; the PIN must never be sent or automated.

Only the two installed QA packages from the previously approved cleanup list were removed: `com.lifetalea.app.debug` and `com.lifetalea.app.debug.test`. Both removals succeeded. Free space increased from 995,372 to 1,099,216 KiB. The regular app was retained; QA APKs and evidence remain in the earlier local archive. No personal files or regular-app data were cleared. The attempted bounded session detected the lock before changing power settings. SDK mode was not changed.

The independent security startup request for source commit `56a89eb2aa7467d9613b3515bc1e84a5da52d80d` stalled without an authoritative scan ID or directory. That single request was stopped. No replacement scan, invented ownership or terminal audit fallback was started, and no independent audit is claimed. The security-scan skill's desktop rule states: “Do not invent scan ownership, start a replacement scan, open setup, or switch to a terminal workflow.”

Read-only provider checks confirmed an active, healthy project with base region `eu-central-1` and active verifier function version 3. All three deployed source files match after normalizing line endings and ignoring one extra final newline. A public health request returned HTTP 200, production readiness and execution-region header `eu-west-2`. This does not prove the region or retention of all requests. The privacy policy and data map now distinguish project base region from globally routed execution. No production service, secrets, quota or logging configuration was changed.

The public draft remains version 4 and was not submitted. No payment was made. Remaining gates include actual version 5 Appstore update/binary/runtime checks; native locale approval and current release assets; independent security and final provider/privacy/store assessment; outstanding app-lock/sorting/theme, backup/crash-recovery, accessibility/performance/device and public billing recovery requirements. Earlier version 5 debug tests retain their dates and scope in `PRODUCT_PRIVACY_RELEASE_REVIEW_2026-11-10.md`.

Evidence: `deliverables/reports/amazon-v5-2026-11-10/`.
