package com.lifetalea.app
import com.lifetalea.app.billing.*
import org.junit.Assert.*
import org.junit.Test
class BillingPolicyTest {
    @Test fun sandboxCannotGrantProductionEntitlements() {
        assertFalse(BillingPolicy.sdkMatches(false, "sandbox", "SANDBOX"))
        assertFalse(BillingPolicy.sdkMatches(false, "production", "UNKNOWN"))
        assertFalse(BillingPolicy.sdkMatches(false, "production", "SANDBOX"))
        assertTrue(BillingPolicy.sdkMatches(true, "sandbox", "SANDBOX"))
        assertTrue(BillingPolicy.sdkMatches(false, "production", "PRODUCTION"))
    }
    private var time = 1000000L
    private fun receipt(id: String = "receipt", user: String = "alice", active: Boolean = true) = VerifiedReceipt(ReceiptClaims(user, id, BillingPolicy.SKU, "production", active, time, time + 60000), "signed-fixture")
    @Test fun accountChangeRejectsLateVerificationAndWrongUser() {
        val session = BillingSession(false,"production") { time }
        val old = session.beginIdentityCheck(); session.identify(old,"alice",null)
        val current = session.beginIdentityCheck(); session.identify(current,"bob",null)
        assertFalse(session.record(old,"alice",receipt()))
        assertFalse(session.record(current,"bob",receipt()))
        assertNull(session.current)
    }
    @Test fun cachesRequireIdentityAndExpireWithoutRestart() {
        val session = BillingSession(false,"production") { time }
        val epoch = session.beginIdentityCheck(); assertNull(session.current)
        session.identify(epoch,"alice",receipt()); assertNotNull(session.current)
        time += 60000; assertNull(session.current)
    }
    @Test fun cancellationRemovesOnlyItsOwnReceiptRegardlessOfOrder() {
        val session = BillingSession(false,"production") { time }; val epoch = session.beginIdentityCheck(); session.identify(epoch,"alice",null)
        session.record(epoch,"alice",receipt("active")); session.record(epoch,"alice",receipt("old",active=false))
        assertEquals("active",session.current!!.claims.receiptId)
        session.record(epoch,"alice",receipt("active",active=false)); assertNull(session.current)
    }
    @Test fun canceledReceiptCannotBeRegrantedByALateActiveAssertion() {
        val session=BillingSession(false,"production") { time };val epoch=session.beginIdentityCheck();session.identify(epoch,"alice",null)
        session.record(epoch,"alice",receipt())
        session.record(epoch,"alice",receipt(active=false))
        assertFalse(session.record(epoch,"alice",receipt()))
        assertNull(session.current)
    }
    @Test fun currentSdkCancellationRevokesOnlyItsBoundReceiptAndBlocksLateGrants() {
        val session=BillingSession(false,"production") { time };val epoch=session.beginIdentityCheck();session.identify(epoch,"alice",receipt())
        assertFalse(session.revoke(epoch,"bob","receipt"));assertNotNull(session.current)
        assertFalse(session.revoke(epoch-1,"alice","receipt"));assertNotNull(session.current)
        assertTrue(session.revoke(epoch,"alice","receipt"));assertNull(session.current)
        assertFalse(session.record(epoch,"alice",receipt()));assertNull(session.current)
        assertTrue(session.record(epoch,"alice",receipt("new-receipt")));assertNotNull(session.current)
    }
    @Test fun completedRestoreRemovesAbsentReceiptsButNetworkFailureCanKeepSeenSignedCache() {
        val session = BillingSession(false,"production") { time }; val epoch = session.beginIdentityCheck(); session.identify(epoch,"alice",receipt())
        session.finishSnapshot(epoch,"alice",setOf("receipt")); assertNotNull(session.current)
        session.finishSnapshot(epoch,"alice",emptySet()); assertNull(session.current)
    }
    @Test fun environmentSkuAndTimeBoundsCannotBeOverriddenByAnAssertion() {
        val c=receipt().claims
        listOf(c.copy(environment="sandbox"),c.copy(sku="other"),c.copy(expiresAt=time),c.copy(issuedAt=time+300001,expiresAt=time+400000),c.copy(expiresAt=time+BillingPolicy.MAX_TTL+1)).forEach {
            assertFalse(BillingPolicy.valid(it,"alice",false,"production",time))
        }
        assertFalse(BillingPolicy.environmentAllowed(false,"sandbox"))
    }
    @Test fun staleSnapshotCannotRevokeNewAccount() {
        val session=BillingSession(false,"production") { time }; val old=session.beginIdentityCheck();session.identify(old,"alice",null)
        val next=session.beginIdentityCheck();session.identify(next,"bob",receipt(user="bob"))
        session.finishSnapshot(old,"alice",emptySet());assertNotNull(session.current)
    }
    @Test fun verifiedTimeDoesNotFollowWallClockRollbackOrForwardChanges() {
        var wall=1000L;var elapsed=20L
        val clock=VerifiedClock({wall},{elapsed});assertEquals(1000L,clock.now)
        clock.anchor(2000,20);wall=0;elapsed=1020;assertEquals(3000L,clock.now)
        wall=Long.MAX_VALUE;elapsed=2020;assertEquals(4000L,clock.now)
    }
    @Test fun malformedSdkUserCannotStartAVerifiedSession() {
        val session=BillingSession(false,"production") { time };val epoch=session.beginIdentityCheck()
        for(user in listOf("","..","a\nb","x".repeat(257))) assertFalse(session.identify(epoch,user,null))
        assertNull(session.current)
    }
}
