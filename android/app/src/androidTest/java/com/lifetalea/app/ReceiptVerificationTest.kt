package com.lifetalea.app

import android.content.Context
import android.content.ContextWrapper
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.lifetalea.app.billing.*
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.security.KeyPairGenerator
import java.security.Signature
import java.util.Base64
import java.util.UUID

@RunWith(AndroidJUnit4::class)
class ReceiptVerificationTest {
    private fun fixture() = JSONObject(InstrumentationRegistry.getInstrumentation().context.assets.open("rvs-contract.json").bufferedReader().use { it.readText() })
    @Test fun nodeSignedReceiptsBindAccountReceiptAndLifetimeOnFire() {
        val f=fixture();val decoder=ReceiptAssertionDecoder(f.getString("publicKey"),"production",false)
        val token=f.getString("active");val user=f.getString("userId");val id=f.getString("receiptId");val now=f.getLong("now")
        assertTrue(decoder.configured);assertTrue(decoder.decode(token,user,id,now)!!.claims.active)
        assertFalse(decoder.decode(f.getString("canceled"),user,id,now)!!.claims.active)
        assertNull(decoder.decode(token,"another-account",id,now));assertNull(decoder.decode(token,user,"another-receipt",now))
        assertNull(decoder.decode(token,user,id,now+3600000));assertNull(decoder.decode(token,user,id,now-300001))
    }
    @Test fun tamperedSignaturesAndEvenValidlySignedBadSchemasAreRejected() {
        val f=fixture();val user=f.getString("userId");val id=f.getString("receiptId");val now=f.getLong("now");val token=f.getString("active")
        val decoder=ReceiptAssertionDecoder(f.getString("publicKey"),"production",false)
        val pieces=token.split('.');assertNull(decoder.decode(pieces[0]+"A."+pieces[1],user,id,now))
        assertNull(decoder.decode(token+".extra",user,id,now))
        val pair=KeyPairGenerator.getInstance("RSA").apply { initialize(2048) }.generateKeyPair()
        val own=ReceiptAssertionDecoder(Base64.getEncoder().encodeToString(pair.public.encoded),"production",false)
        val payload=String(Base64.getUrlDecoder().decode(pieces[0]),Charsets.UTF_8)
        fun signed(json: JSONObject): String {
            val data=Base64.getUrlEncoder().withoutPadding().encodeToString(json.toString().toByteArray(Charsets.UTF_8))
            val signature=Signature.getInstance("SHA256withRSA").apply { initSign(pair.private);update(data.toByteArray(Charsets.US_ASCII)) }.sign()
            return data+"."+Base64.getUrlEncoder().withoutPadding().encodeToString(signature)
        }
        assertNull(own.decode(token,user,id,now))
        listOf("active" to "true", "iss" to "other", "aud" to "another.app", "iat" to now.toString(), "exp" to now+BillingPolicy.MAX_TTL+1, "sku" to "another.product").forEach { (key,value) ->
            assertNull(own.decode(signed(JSONObject(payload).put(key,value)),user,id,now))
        }
    }
    @Test fun sandboxAndUntrustedEndpointConfigurationCannotUnlockRelease() {
        val f=fixture();val key=f.getString("publicKey");val now=f.getLong("now");val user=f.getString("userId")
        assertNull(ReceiptAssertionDecoder(key,"production",false).decode(f.getString("sandbox"),user,null,now))
        assertFalse(ReceiptAssertionDecoder(key,"sandbox",false).configured)
        assertNotNull(ReceiptAssertionDecoder(key,"sandbox",true).decode(f.getString("sandbox"),user,null,now))
        for(url in listOf("http://localhost/v1/verify","https://example.com/v1/verify?secret=no","https://user@example.com/v1/verify","https://example.com/wrong")) {
            assertFalse(HttpsReceiptGateway(url,key,"production",false).configured)
        }
        assertFalse(HttpsReceiptGateway("https://example.com/v1/verify","","production",false).configured)
    }
    @Test fun legacyPremiumPreferenceCannotGrantAndMissingVerifierNeverStartsPurchaseFlow() {
        val target=InstrumentationRegistry.getInstrumentation().targetContext;val name="billing-test-${UUID.randomUUID()}"
        val context=object:ContextWrapper(target) { override fun getSharedPreferences(ignored:String,mode:Int)=target.getSharedPreferences(name,Context.MODE_PRIVATE) }
        context.getSharedPreferences(name,0).edit().putBoolean("premium",true).putString("user","fixture-user").commit()
        val billing=AmazonBilling(context,HttpsReceiptGateway("","","production",true))
        try { billing.initialize();billing.refresh();billing.purchase();billing.restore();assertFalse(billing.state.value.premium);assertFalse(billing.state.value.available) }
        finally { billing.close();target.deleteSharedPreferences(name) }
    }
}
