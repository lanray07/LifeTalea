package com.lifetalea.app.billing

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import org.json.JSONObject
import java.net.URI
import java.security.KeyFactory
import java.security.Signature
import java.security.interfaces.RSAPublicKey
import java.security.spec.X509EncodedKeySpec
import java.util.Base64
import javax.net.ssl.HttpsURLConnection

data class ReceiptClaims(val user: String, val receiptId: String, val sku: String, val environment: String, val active: Boolean, val issuedAt: Long, val expiresAt: Long)
data class VerifiedReceipt(val claims: ReceiptClaims, val assertion: String)

/** Once verified, device wall-clock changes cannot extend an in-process entitlement. */
class VerifiedClock(private val wall: () -> Long, private val elapsed: () -> Long) {
    private var serverTime: Long? = null
    private var observedElapsed = 0L
    val now: Long get() = serverTime?.let { it + (elapsed() - observedElapsed).coerceAtLeast(0) } ?: wall()
    fun anchor(time: Long, observed: Long) { require(time >= 0 && observed >= 0); serverTime = time; observedElapsed = observed }
}

object BillingPolicy {
    const val SKU = "com.lifetalea.premium"
    const val MAX_TTL = 24L * 60 * 60 * 1000
    fun environmentAllowed(debug: Boolean, environment: String) = environment == "production" || (debug && environment == "sandbox")
    fun sdkMatches(debug: Boolean, environment: String, sdkMode: String) = environmentAllowed(debug, environment) &&
        ((environment == "production" && sdkMode == "PRODUCTION") || (debug && environment == "sandbox" && sdkMode == "SANDBOX"))
    fun valid(claims: ReceiptClaims, user: String, debug: Boolean, environment: String, now: Long): Boolean =
        user.isNotBlank() && user.length <= 256 && environmentAllowed(debug, environment) && claims.environment == environment && claims.user == user && claims.sku == SKU &&
            claims.receiptId.isNotBlank() && claims.receiptId.length <= 512 && claims.issuedAt >= 0 && claims.issuedAt <= now + 300000 &&
            claims.expiresAt > now && claims.expiresAt > claims.issuedAt && claims.expiresAt - claims.issuedAt <= MAX_TTL
}

/** Every verified result is bound to an identity generation; late results cannot switch accounts. */
class BillingSession(private val debug: Boolean, private val environment: String, private val now: () -> Long = System::currentTimeMillis) {
    var generation = 0L; private set
    var user: String? = null; private set
    private val receipts = linkedMapOf<String, VerifiedReceipt>()
    private val canceled = mutableSetOf<String>()
    val current: VerifiedReceipt? get() = user?.let { id -> receipts.values.filter { it.claims.active && BillingPolicy.valid(it.claims, id, debug, environment, now()) }.maxByOrNull { it.claims.issuedAt } }
    fun beginIdentityCheck(): Long { generation++; user = null; receipts.clear(); canceled.clear(); return generation }
    fun identify(epoch: Long, id: String, cached: VerifiedReceipt?): Boolean {
        if (epoch != generation || id.isBlank() || id.length > 256 || id.any { it.code !in 33..126 } || id in listOf(".", "..")) return false
        user = id
        cached?.let { record(epoch, id, it) }
        return true
    }
    fun record(epoch: Long, id: String, receipt: VerifiedReceipt): Boolean {
        if (epoch != generation || user != id || !BillingPolicy.valid(receipt.claims, id, debug, environment, now())) return false
        if (receipt.claims.active) {
            if (receipt.claims.receiptId in canceled) return false
            receipts[receipt.claims.receiptId] = receipt
        } else revoke(epoch, id, receipt.claims.receiptId)
        return true
    }
    /** Current-account SDK cancellation can deny access; it can never grant it. */
    fun revoke(epoch: Long, id: String, receiptId: String): Boolean {
        if (epoch != generation || user != id || receiptId.isBlank() || receiptId.length > 512) return false
        canceled.add(receiptId); receipts.remove(receiptId)
        return true
    }
    fun finishSnapshot(epoch: Long, id: String, receiptIds: Set<String>) {
        if (epoch == generation && user == id) receipts.keys.retainAll(receiptIds)
    }
}

class ReceiptAssertionDecoder(publicKeyBase64: String, private val environment: String, private val debug: Boolean) {
    private val publicKey = runCatching {
        (KeyFactory.getInstance("RSA").generatePublic(X509EncodedKeySpec(Base64.getDecoder().decode(publicKeyBase64))) as RSAPublicKey).also { require(it.modulus.bitLength() >= 2048) }
    }.getOrNull()
    val configured get() = publicKey != null && BillingPolicy.environmentAllowed(debug, environment)
    fun decode(assertion: String, user: String, receiptId: String? = null, now: Long = System.currentTimeMillis()): VerifiedReceipt? = runCatching {
        require(configured && assertion.length <= 16384)
        val parts = assertion.split('.'); require(parts.size == 2 && parts.all { it.matches(Regex("[A-Za-z0-9_-]+")) })
        val signature = Signature.getInstance("SHA256withRSA").apply { initVerify(publicKey); update(parts[0].toByteArray(Charsets.US_ASCII)) }
        require(signature.verify(Base64.getUrlDecoder().decode(parts[1])))
        val payload = Base64.getUrlDecoder().decode(parts[0]); require(payload.size <= 8192)
        val json = JSONObject(String(payload, Charsets.UTF_8))
        fun text(key: String) = json.get(key) as String
        fun number(key: String): Long = (json.get(key) as Number).let { require(it.toDouble() == it.toLong().toDouble()); it.toLong() }
        require(number("v") == 1L && text("iss") == "lifetalea-amazon-rvs" && text("aud") == "com.lifetalea.app")
        require(json.get("testTransaction") is Boolean && json.get("betaProduct") is Boolean)
        val claims = ReceiptClaims(text("sub"), text("receiptId"), text("sku"), text("environment"), json.get("active") as Boolean, number("iat"), number("exp"))
        require(BillingPolicy.valid(claims, user, debug, environment, now) && (receiptId == null || receiptId == claims.receiptId))
        VerifiedReceipt(claims, assertion)
    }.getOrNull()
}

interface ReceiptGateway {
    val configured: Boolean
    val environment: String
    fun cached(assertion: String, user: String, now: Long = System.currentTimeMillis()): VerifiedReceipt?
    suspend fun verify(user: String, receiptId: String): VerifiedReceipt
}

/** Platform TLS trust only: no cleartext, custom trust manager or redirect fallback. */
class HttpsReceiptGateway(private val endpoint: String, publicKeyBase64: String, override val environment: String, debug: Boolean) : ReceiptGateway {
    private val decoder = ReceiptAssertionDecoder(publicKeyBase64, environment, debug)
    private val uri = runCatching { URI(endpoint).also { require(it.scheme == "https" && !it.host.isNullOrBlank() && it.rawUserInfo == null && it.rawQuery == null && it.rawFragment == null && it.path.endsWith("/v1/verify")) } }.getOrNull()
    override val configured get() = uri != null && decoder.configured
    override fun cached(assertion: String, user: String, now: Long) = decoder.decode(assertion, user, now = now)
    override suspend fun verify(user: String, receiptId: String): VerifiedReceipt = withTimeout(15000) { withContext(Dispatchers.IO) {
        check(configured)
        require(user.length in 1..256 && receiptId.length in 1..512)
        val connection = uri!!.toURL().openConnection() as HttpsURLConnection
        try {
            connection.requestMethod = "POST"; connection.instanceFollowRedirects = false
            connection.connectTimeout = 8000; connection.readTimeout = 5000; connection.doOutput = true
            connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
            val body = JSONObject().put("userId", user).put("receiptId", receiptId).toString().toByteArray(Charsets.UTF_8)
            connection.setFixedLengthStreamingMode(body.size)
            connection.outputStream.use { it.write(body) }
            require(connection.responseCode == 200)
            require(connection.contentLength <= 16384)
            val output = java.io.ByteArrayOutputStream()
            connection.inputStream.use { input ->
                val buffer = ByteArray(2048)
                while (true) { currentCoroutineContext().ensureActive(); val count = input.read(buffer); if (count < 0) break; require(output.size() + count <= 16384); output.write(buffer, 0, count) }
            }
            val json = JSONObject(output.toString("UTF-8"))
            decoder.decode(json.getString("assertion"), user, receiptId) ?: error("Receipt assertion rejected")
        } finally { connection.disconnect() }
    } }
}
