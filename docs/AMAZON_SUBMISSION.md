Current update — 4 November 2026: the isolated Supabase verifier is deployed; Premium is Approved for TEST at GBP4.99 plus calculated prices; the configured billing LAT release is submitted. No real LAT purchase or public launch is verified. The older audit below remains historical. Current evidence and outstanding gates are in RELEASE_READINESS.md, AMAZON_SUPABASE_DEPLOYMENT.md and amazon-console-review.json.

# Amazon submission preparation

Release status must be taken from RELEASE_READINESS.md, not inferred from the presence of an APK. Do not submit or publish until authorised and all mandatory gates pass.

Publisher: O.Bankole. Support: banksmi@mail.com. Candidate package: com.lifetalea.app. Version: 0.1.0 (1). Candidate Premium SKU: com.lifetalea.premium, ENTITLED, proposed UK test price £4.99. Confirm these in the correct Amazon app; the ambient open console tab alone does not prove it belongs to this app.

Repository: https://github.com/lanray07/LifeTalea

Policy source URL after push: https://github.com/lanray07/LifeTalea/blob/main/docs/PRIVACY_POLICY.md

Support source URL after push: https://github.com/lanray07/LifeTalea/blob/main/docs/SUPPORT.md

Current official field/screenshot requirements and limitations are in RESEARCH.md and deliverables/store-assets/metadata/REQUIREMENTS.json. Verify console locale variants and title limits before submission. Keep app languages, listing languages and country availability separate. No live Appstore download URL is invented.

Before submission: confirm identity/name clearance; configure correct public app PEM and entitlement; complete receipt verification and purchase scenarios; finish translation/native review; generate all eight actual-screen compositions per approved listing locale; inspect required Fire hardware/orientations; finish accessibility/privacy/security checks; verify release signature and upgrade identity; review screenshot and description claims; approve final legal disclosures. Phone compatibility requires a separate distribution plan because Amazon's non-Fire Android Appstore ended in 2025.

Updated local review bundle: run `python scripts/inspect_amazon_apk.py`, then `python scripts/prepare_amazon_submission.py` after current build/device/capture checks. Verify with `python scripts/prepare_amazon_submission.py --check`. The ZIP is ignored by Git; its audit/index are tracked. See AMAZON_OWNER_ACTIONS.md and AMAZON_TESTING_INSTRUCTIONS.txt. The console was inspected read-only on 3 November: zero in-app items, empty testing instructions and unchecked export compliance remain. The existing public app PEM was downloaded and bundled locally; no console fields were changed.
