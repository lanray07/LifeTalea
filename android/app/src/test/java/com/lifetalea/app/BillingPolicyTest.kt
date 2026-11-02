package com.lifetalea.app
import com.lifetalea.app.billing.BillingPolicy
import org.junit.Assert.*
import org.junit.Test
class BillingPolicyTest {
    @Test fun sandboxCannotGrantProductionEntitlements() {
        assertFalse(BillingPolicy.canGrant(false, "SANDBOX")); assertFalse(BillingPolicy.canGrant(false, "UNKNOWN"))
        assertTrue(BillingPolicy.canGrant(true, "SANDBOX")); assertTrue(BillingPolicy.canGrant(false, "PRODUCTION"))
    }
}
