package com.lifetalea.app.billing

import android.content.Context
import android.os.SystemClock
import android.provider.Settings
import com.amazon.device.iap.*
import com.amazon.device.iap.model.*
import com.amazon.device.drm.LicensingService
import com.lifetalea.app.BuildConfig
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

data class BillingState(val premium: Boolean = false, val price: String? = null, val available: Boolean = false, val message: String = "billing_unconfigured")

class AmazonBilling(private val context: Context, private val gateway: ReceiptGateway = HttpsReceiptGateway(BuildConfig.RVS_URL, BuildConfig.RVS_PUBLIC_KEY, BuildConfig.RVS_ENVIRONMENT, BuildConfig.DEBUG)) : PurchasingListener {
    companion object { const val SKU = BillingPolicy.SKU }
    private val prefs = context.getSharedPreferences(if (BuildConfig.DEBUG) "iap_debug" else "iap_production", Context.MODE_PRIVATE)
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private val clock = VerifiedClock(System::currentTimeMillis, SystemClock::elapsedRealtime)
    private val session = BillingSession(BuildConfig.DEBUG, gateway.environment) { clock.now }
    private val bootCount get() = runCatching { Settings.Global.getInt(context.contentResolver, "boot_count", -1) }.getOrDefault(-1)
    val state = MutableStateFlow(BillingState())
    private val publicKeyPresent = runCatching { context.assets.open("AppstoreAuthenticationKey.pem").use { require(it.read() >= 0) }; true }.getOrDefault(false)
    private var initialized = false
    private var productReady = false
    private var refreshing = false
    private var userRequest: Pair<Long, RequestId>? = null
    private var productRequest: Pair<Long, RequestId>? = null
    private var updatesRequest: Pair<Long, RequestId>? = null
    private var purchaseRequest: Pair<String, RequestId>? = null
    private var pendingPurchase: Pair<String, String>? = null
    private var timeout: Job? = null
    private var expiry: Job? = null
    private val history = linkedMapOf<String, Receipt>()
    private var pages = 0
    private val verificationMutex = Mutex()
    private val newPurchases = mutableSetOf<String>()

    private fun modeMatches() = runCatching { BillingPolicy.sdkMatches(BuildConfig.DEBUG, gateway.environment, LicensingService.getAppstoreSDKMode()) }.getOrDefault(false)
    private fun cached(user: String): VerifiedReceipt? {
        val assertion = prefs.getString("assertion", null) ?: return null
        val boot = bootCount
        if (boot < 0 || prefs.getInt("assertion_boot", -2) != boot) return null
        val observed = prefs.getLong("assertion_elapsed", -1)
        val serverTime = prefs.getLong("assertion_issued", -1)
        val delta = SystemClock.elapsedRealtime() - observed
        if (observed < 0 || serverTime < 0 || delta !in 0..BillingPolicy.MAX_TTL) return null
        val receipt = gateway.cached(assertion, user, serverTime + delta) ?: return null
        if (receipt.claims.issuedAt != serverTime) return null
        clock.anchor(serverTime, observed)
        return receipt
    }
    private fun publish(message: String = "free_tier") {
        val active = session.current
        state.value = state.value.copy(premium = active != null, available = initialized && gateway.configured && BuildConfig.AMAZON_PURCHASES_ENABLED && modeMatches() && productReady && session.user != null && !refreshing && purchaseRequest == null,
            message = if (active != null) "premium_active" else message)
        prefs.edit().remove("premium").remove("user").apply {
            if (active != null && prefs.getString("assertion", null) != active.assertion) {
                putString("assertion", active.assertion); putLong("assertion_issued", active.claims.issuedAt)
                putLong("assertion_elapsed", SystemClock.elapsedRealtime()); putInt("assertion_boot", bootCount)
            } else if (active == null && session.user != null) remove("assertion")
        }.apply()
        expiry?.cancel()
        if (active != null) expiry = scope.launch { delay((active.claims.expiresAt - clock.now).coerceIn(1, 30000)); publish() }
    }
    fun initialize() {
        if (!publicKeyPresent || !gateway.configured) return
        runCatching {
            PurchasingService.registerListener(context.applicationContext, this)
            initialized = true
            LicensingService.verifyLicense(context.applicationContext) { _ -> scope.launch { refresh() } }
        }.onFailure { state.value = state.value.copy(message = "billing_unavailable") }
    }
    private fun watch(epoch: Long) {
        timeout?.cancel()
        timeout = scope.launch { delay(20000); if (session.generation == epoch) { refreshing = false; userRequest = null; updatesRequest = null; publish("billing_unavailable") } }
    }
    fun refresh() {
        if (!initialized || !gateway.configured) { state.value = state.value.copy(premium = false, available = false, message = "billing_unconfigured"); return }
        val epoch = session.beginIdentityCheck()
        expiry?.cancel()
        refreshing = true; productReady = false; history.clear(); newPurchases.clear(); pages = 0
        state.value = state.value.copy(premium = false, available = false)
        runCatching { userRequest = epoch to PurchasingService.getUserData(); watch(epoch) }
            .onFailure { refreshing = false; publish("billing_unavailable") }
    }
    fun purchase() {
        val user = session.user ?: return
        if (!state.value.available || state.value.premium) return
        runCatching { purchaseRequest = user to PurchasingService.purchase(SKU); publish("one_time") }
            .onFailure { purchaseRequest = null; publish("purchase_failed") }
    }
    fun restore() = refresh()
    override fun onUserDataResponse(response: UserDataResponse) {
        val request = userRequest ?: return
        if (request.second != response.requestId || request.first != session.generation) return
        userRequest = null
        if (response.requestStatus != UserDataResponse.RequestStatus.SUCCESSFUL || !modeMatches()) {
            refreshing = false; timeout?.cancel(); publish("billing_unavailable"); return
        }
        val user = response.userData.userId
        if (purchaseRequest?.first != null && purchaseRequest?.first != user) { purchaseRequest = null; pendingPurchase = null }
        if (!session.identify(request.first, user, cached(user))) { refreshing = false; timeout?.cancel(); publish("billing_unavailable"); return }
        publish()
        runCatching {
            productRequest = request.first to PurchasingService.getProductData(setOf(SKU))
            updatesRequest = request.first to PurchasingService.getPurchaseUpdates(true)
            watch(request.first)
        }.onFailure { refreshing = false; publish("billing_unavailable") }
        pendingPurchase?.let { pending -> pendingPurchase = null; if (pending.first == user) verifyPurchase(request.first, user, pending.second) }
    }
    override fun onProductDataResponse(response: ProductDataResponse) {
        val request = productRequest ?: return
        if (request.second != response.requestId || request.first != session.generation) return
        productRequest = null
        val product = response.productData?.get(SKU)
        productReady = response.requestStatus == ProductDataResponse.RequestStatus.SUCCESSFUL && product?.productType == ProductType.ENTITLED
        state.value = state.value.copy(price = if (productReady) product?.price else null)
        publish(if (productReady) "one_time" else "billing_unavailable")
    }
    override fun onPurchaseResponse(response: PurchaseResponse) {
        val request = purchaseRequest ?: return
        if (request.second != response.requestId) return
        purchaseRequest = null
        val receipt = response.receipt
        if (response.requestStatus != PurchaseResponse.RequestStatus.SUCCESSFUL || response.userData.userId != request.first || receipt == null || receipt.sku != SKU || receipt.productType != ProductType.ENTITLED) {
            publish("purchase_failed"); return
        }
        if (session.user == request.first) verifyPurchase(session.generation, request.first, receipt.receiptId)
        else { pendingPurchase = request.first to receipt.receiptId; if (!refreshing) refresh() }
    }
    private fun verifyPurchase(epoch: Long, user: String, receiptId: String) = scope.launch {
        try {
            val verified = verifyBound(epoch, user, receiptId)
            if (session.record(epoch, user, verified)) {
                if (verified.claims.active) newPurchases.add(receiptId) else newPurchases.remove(receiptId)
                publish()
                if (verified.claims.active) runCatching { PurchasingService.notifyFulfillment(receiptId, FulfillmentResult.FULFILLED) }
            }
        } catch (error: Exception) { if (error is CancellationException && error !is TimeoutCancellationException) throw error; if (epoch == session.generation && user == session.user) publish("purchase_failed") }
    }
    private suspend fun verifyBound(epoch: Long, user: String, receiptId: String) = verificationMutex.withLock {
        if (epoch != session.generation || user != session.user) throw CancellationException("Stale billing identity")
        gateway.verify(user, receiptId).also {
            if (epoch != session.generation || user != session.user) throw CancellationException("Stale billing identity")
            clock.anchor(it.claims.issuedAt, SystemClock.elapsedRealtime())
        }
    }
    override fun onPurchaseUpdatesResponse(response: PurchaseUpdatesResponse) {
        val request = updatesRequest ?: return
        if (request.second != response.requestId || request.first != session.generation) return
        updatesRequest = null
        val user = session.user
        if (response.requestStatus != PurchaseUpdatesResponse.RequestStatus.SUCCESSFUL || user == null || response.userData.userId != user) {
            refreshing = false; timeout?.cancel(); publish("billing_unavailable"); return
        }
        response.receipts.filter { it.sku == SKU && it.productType == ProductType.ENTITLED }.forEach { history[it.receiptId] = it }
        if (++pages > 100 || history.size > 100) { refreshing = false; timeout?.cancel(); publish("billing_unavailable"); return }
        if (response.hasMore()) {
            runCatching { updatesRequest = request.first to PurchasingService.getPurchaseUpdates(false); watch(request.first) }
                .onFailure { refreshing = false; publish("billing_unavailable") }
            return
        }
        timeout?.cancel()
        val receipts = history.keys.toList()
        scope.launch {
            var unavailable = false
            try {
                withTimeout(30000) {
                    for (id in receipts) {
                        if (request.first != session.generation || user != session.user) return@withTimeout
                        try {
                            val verified = verifyBound(request.first, user, id)
                            if (session.record(request.first, user, verified)) {
                                publish()
                                if (verified.claims.active) runCatching { PurchasingService.notifyFulfillment(id, FulfillmentResult.FULFILLED) }
                            }
                        } catch (error: Exception) { if (error is CancellationException) throw error; unavailable = true }
                    }
                }
            } catch (_: TimeoutCancellationException) { unavailable = true }
            finally {
                if (scope.isActive && request.first == session.generation && user == session.user) {
                    session.finishSnapshot(request.first, user, receipts.toSet() + newPurchases)
                    if (session.current != null) purchaseRequest = null
                    refreshing = false; publish(if (unavailable) "billing_unavailable" else "free_tier")
                }
            }
        }
    }
    fun close() {
        initialized = false; session.beginIdentityCheck()
        userRequest = null; productRequest = null; updatesRequest = null; purchaseRequest = null; pendingPurchase = null
        scope.cancel()
    }
}
