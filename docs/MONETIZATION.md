# Monetisation

Working model: freemium with a one-time Amazon entitlement, SKU `com.lifetalea.premium`. Proposed UK test price £4.99 is a commercial hypothesis. No product or price was created or changed in the console.

Free functionality includes three albums, unlimited written memories, photographs, timeline, scrapbook drafts, short recordings and basic backup/restore. Premium gates extra albums, longer recordings, PDF exports and encrypted backup creation. Deletion, ordinary access and basic backups never require a purchase. Advanced cloud transcription is not promised as a perpetual one-time benefit.

The pinned Amazon SDK retrieves localised prices, initiates purchases, receives callbacks, paginates restore history and persists entitlements. A missing app-specific authentication PEM disables purchasing. Licence initialisation precedes SDK mode checks; production grants reject sandbox/unknown mode. Debug entitlements and the debug package are separate from production.

Live verification is BLOCKED until the correct public PEM, product type ENTITLED, SKU, marketplace price and test configuration are available. Cancellation, failures, restoration, refunds, account changes and offline reconciliation must be exercised through App Tester/DevTest and LAT. A pure unit test of mode isolation does not validate live purchases. No server-side RVS service is implemented yet.

Amazon no longer distributes through its Appstore on non-Amazon Android phones. A future phone distribution build requires a selected channel and its compliant billing integration; do not add Google Play Billing to the Fire build.
