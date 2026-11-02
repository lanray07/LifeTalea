package com.lifetalea.app.billing

import android.content.Context
import com.amazon.device.iap.*
import com.amazon.device.iap.model.*
import com.amazon.device.drm.LicensingService
import com.lifetalea.app.BuildConfig
import kotlinx.coroutines.flow.MutableStateFlow

data class BillingState(val premium: Boolean = false, val price: String? = null, val available: Boolean = false, val message: String = "billing_unconfigured")
class AmazonBilling(private val context: Context) : PurchasingListener {
    companion object { const val SKU = "com.lifetalea.premium" }
    private val prefs = context.getSharedPreferences(if (BuildConfig.DEBUG) "iap_debug" else "iap_production", Context.MODE_PRIVATE)
    val state = MutableStateFlow(BillingState(premium = prefs.getBoolean("premium", false)))
    private var userId: String? = null
    private var restoring = false
    private var restored = false
    private val configured = runCatching { context.assets.open("AppstoreAuthenticationKey.pem").use { it.read() }; true }.getOrDefault(false)
    fun initialize() {
        if (!configured) return
        runCatching {
            LicensingService.verifyLicense(context.applicationContext) { _ ->
                // Initialises SDK mode; a licence failure never locks the local library.
            }
            PurchasingService.registerListener(context.applicationContext, this)
        }.onFailure { state.value = state.value.copy(message = "billing_unavailable") }
    }
    fun refresh() {
        if (!configured) return
        runCatching { PurchasingService.getUserData(); PurchasingService.getProductData(setOf(SKU)); PurchasingService.getPurchaseUpdates(false) }
            .onFailure { state.value = state.value.copy(available = false, message = "billing_unavailable") }
    }
    fun purchase() { if (state.value.available && userId != null) runCatching { PurchasingService.purchase(SKU) }.onFailure { state.value = state.value.copy(message = "purchase_failed") } }
    fun restore() {
        if (!configured) { state.value = state.value.copy(message = "billing_unconfigured"); return }
        restoring = true; restored = false
        runCatching { PurchasingService.getPurchaseUpdates(true) }.onFailure { restoring = false; state.value = state.value.copy(message = "purchase_failed") }
    }
    private fun grant(value: Boolean, user: String) {
        // Sandbox entitlements live only in debug storage and can never grant production access.
        if (!BillingPolicy.canGrant(BuildConfig.DEBUG, LicensingService.getAppstoreSDKMode())) return
        prefs.edit().putBoolean("premium", value).putString("user", user).apply()
        state.value = state.value.copy(premium = value, message = if (value) "premium_active" else "free_tier")
    }
    override fun onUserDataResponse(response: UserDataResponse) {
        if (response.requestStatus == UserDataResponse.RequestStatus.SUCCESSFUL) {
            userId = response.userData.userId
            if (prefs.getString("user", null) != userId) grant(false, userId!!)
        } else state.value = state.value.copy(available = false, message = "billing_unavailable")
    }
    override fun onProductDataResponse(response: ProductDataResponse) {
        val product = response.productData?.get(SKU)
        val ok = response.requestStatus == ProductDataResponse.RequestStatus.SUCCESSFUL && product?.productType == ProductType.ENTITLED
        state.value = state.value.copy(price = if (ok) product?.price else null, available = ok, message = if (ok) "one_time" else "billing_unavailable")
    }
    override fun onPurchaseResponse(response: PurchaseResponse) {
        val receipt = response.receipt
        if (response.requestStatus == PurchaseResponse.RequestStatus.SUCCESSFUL && receipt != null && receipt.sku == SKU && receipt.productType == ProductType.ENTITLED) {
            grant(!receipt.isCanceled, response.userData.userId)
            if (state.value.premium) PurchasingService.notifyFulfillment(receipt.receiptId, FulfillmentResult.FULFILLED)
        } else state.value = state.value.copy(message = "purchase_failed")
    }
    override fun onPurchaseUpdatesResponse(response: PurchaseUpdatesResponse) {
        if (response.requestStatus != PurchaseUpdatesResponse.RequestStatus.SUCCESSFUL) { restoring = false; state.value = state.value.copy(message = "purchase_failed"); return }
        response.receipts.filter { it.sku == SKU && it.productType == ProductType.ENTITLED }.forEach {
            if (restoring) restored = !it.isCanceled else grant(!it.isCanceled, response.userData.userId)
        }
        if (response.hasMore()) PurchasingService.getPurchaseUpdates(false)
        else if (restoring) { grant(restored, response.userData.userId); restoring = false }
    }
}
object BillingPolicy {
    fun canGrant(debug: Boolean, sdkMode: String) = sdkMode == "PRODUCTION" || (debug && sdkMode == "SANDBOX")
}
