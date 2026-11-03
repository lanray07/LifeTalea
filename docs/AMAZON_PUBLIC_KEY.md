# LifeTalea public Appstore authentication key

Retrieved through the signed-in Amazon console on 3 November 2026, after verifying the visible LifeTalea title, app ID `amzn1.devportal.mobileapp.035a0c55782f4cd68dd2453e79fd420e` and release ID `amzn1.devportal.apprelease.103d2ab34c5f43a6b6ba6133db46f7c8`.

The existing **View public key → Download AppstoreAuthenticationKey.pem** control supplied the file. No new key, app, product or account setting was created. The downloaded key was parsed as an RSA 2048-bit **public** key and copied, without reconstruction, to `android/app/src/main/assets/AppstoreAuthenticationKey.pem`.

File SHA-256: `056a8be292f26e52de2b81951b3b51c762c02879dd94fbd35ffad56e994ba40b`.

This public key is intentionally bundled in the APK and may be version controlled. It is separate from an Amazon developer shared secret, private signing key or receipt-verification credential. None of those private credentials was retrieved or added. Do not reuse the PEM for another app.

Bundling the key closes the missing-public-key configuration gap. It does not implement server receipt verification, create the missing entitlement product, validate signing/update identity, or establish successful Amazon purchases. Production purchase availability remains disabled in code until verified fulfillment exists. Check `amazon-release-apk-inspection.json` for the key hash inside the final APK.
