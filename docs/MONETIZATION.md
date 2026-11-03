# Monetisation

Working model: freemium with a one-time Amazon entitlement, SKU `com.lifetalea.premium`. Proposed UK test price £4.99 is a commercial hypothesis. No product or price was created or changed in the console.

Free functionality includes three albums, unlimited written memories, photographs, timeline, scrapbook drafts, short recordings and basic backup/restore. Premium gates extra albums, longer recordings, PDF exports and encrypted backup creation. Deletion, ordinary access and basic backups never require a purchase. Advanced cloud transcription is not promised as a perpetual one-time benefit.

The pinned Amazon SDK adapter retrieves localised prices and supports a separate debug App Tester flow. A missing app-specific public authentication PEM disables SDK initialisation. Production purchase availability and SDK-only production grants are deliberately disabled until server-side RVS is implemented; supplying a PEM does not bypass that gate. A previously cached production Premium boolean is no longer treated as verified entitlement proof. No production purchase should be taken before verified fulfillment is available. Local stories remain accessible.

The debug sandbox adapter binds purchase/update responses to the current SDK user, obtains user identity before requesting the full restore history, and aggregates active receipts across restore pages. These source changes and the mode policy unit test do not prove real Amazon callbacks or account-switch behavior. Those need configured device tests.
The app-specific public PEM is now bundled (see AMAZON_PUBLIC_KEY.md). Live verification remains BLOCKED: the verified console contains zero in-app items, and product type ENTITLED, SKU, marketplace prices and test configuration still need to be configured. Cancellation, failures, restoration, refunds, account changes and offline reconciliation must be exercised through App Tester/DevTest and LAT. A pure unit test of mode isolation does not validate live purchases. No server-side RVS service is implemented yet.

Amazon no longer distributes through its Appstore on non-Amazon Android phones. A future phone distribution build requires a selected channel and its compliant billing integration; do not add Google Play Billing to the Fire build.
