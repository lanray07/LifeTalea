# LifeTalea development privacy notice

Publisher: O.Bankole. Contact: banksmi@mail.com. Effective draft: 4 November 2026. Source: https://github.com/lanray07/LifeTalea.

LifeTalea is in development. This notice describes current implementation and needs legal review against the final release. It is not a claim of compliance certification.

Memories, transcripts, tags, manually entered locations, imported photographs, audio and scrapbook drafts are stored in private application storage on your device. No LifeTalea account is required. There are no advertising or analytics SDKs. The app does not collect your location automatically. Android automatic app backup is disabled.

Microphone access is requested for user-initiated recording or push-to-talk. Saved stories remain local. LifeTalea does not retain raw audio commands. Your installed speech-recognition service may process speech externally and may need internet. Review that service's privacy terms before choosing voice commands. Text and touch controls are available instead. Spoken playback uses your installed TextToSpeech engine; its behaviour depends on that service.

The Amazon Appstore SDK may contact Amazon when the app opens to initialise licensing and refresh account/product information, as well as during a purchase or restore. Amazon purchasing uses Amazon account/product/receipt information to determine Premium access. A receipt verifier is deployed on Supabase. The standard app build still disables initiating purchases pending release testing; the separate Amazon LAT candidate uses that verifier. When configured, LifeTalea sends the Amazon app-specific user ID and receipt ID over HTTPS to its private verifier, which checks them with Amazon and returns a signed, expiring entitlement. No memories, recordings or photos are accepted by that service. The app caches the signed receipt assertion in private storage. The verifier has no customer-content database; the Supabase adapter stores only a shared quota counter and timestamp, without customer/receipt/IP identifiers. Supabase and its infrastructure may process connection metadata and operational logs. Final logging, retention, regional processing and provider disclosures still require assessment before public launch. Amazon retains its transaction records under its own policies. Memories and media are not sent as part of purchasing.

Automatic file transcription and cloud sync are not configured. LifeTalea does not currently upload stories to a transcription provider.

When you export a PDF or backup you choose the destination through Android's document picker. If that destination is a cloud provider, that provider handles the selected export under its policies. Unencrypted archives contain readable personal content. Optional passphrase encryption protects selected archives, not the separately stored local database. Keep passphrases and backup copies safe. No end-to-end encryption claim is made.

Delete individual content in the app, or use Settings → Delete all local data to remove the local library. Uninstalling also removes private local app data. Exported files remain wherever you saved them and must be deleted separately. Deleting local memories does not remove Amazon transaction records or any file held by another person/provider.

There is no public feed or automatic publication. Obtain permission from people whose voices, photographs or stories you preserve. When contacting support, avoid sending private memories, recordings, backups or passphrases. The marketing preview has no contact submission form and no analytics integration; hosting providers may maintain their own access logs once deployed.
