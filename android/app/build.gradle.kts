import java.security.KeyFactory
import java.security.interfaces.RSAPublicKey
import java.security.spec.X509EncodedKeySpec
import java.util.Base64
import java.security.MessageDigest
import java.io.File
import java.net.URI
import java.nio.file.Files
import java.nio.file.StandardCopyOption

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("com.google.devtools.ksp")
}
val receiptUrl = providers.gradleProperty("lifetaleaRvsUrl").getOrElse("")
val receiptPublicKey = providers.gradleProperty("lifetaleaRvsPublicKey").getOrElse("")
val receiptEnvironment = providers.gradleProperty("lifetaleaRvsEnvironment").getOrElse("production")
val purchasesEnabled = providers.gradleProperty("lifetaleaPurchasesEnabled").getOrElse("false")
val billingQaPublicKey = providers.gradleProperty("lifetaleaBillingQaPublicKey").getOrElse("")
require(billingQaPublicKey.isEmpty() || (billingQaPublicKey.length <= 4096 && billingQaPublicKey.matches(Regex("[A-Za-z0-9+/=]+")))) { "Invalid public sandbox signing key" }
require(receiptUrl.isEmpty() || (receiptUrl.length <= 512 && receiptUrl.matches(Regex("https://[A-Za-z0-9.-]+(?::[0-9]{1,5})?/[A-Za-z0-9/_-]*v1/verify")))) { "Use a public HTTPS verifier URL without credentials, query or fragment" }
require(receiptEnvironment in listOf("production", "sandbox") && purchasesEnabled in listOf("true", "false")) { "Invalid public billing build configuration" }
if (receiptPublicKey.isNotEmpty()) {
    val publicKey = runCatching { KeyFactory.getInstance("RSA").generatePublic(X509EncodedKeySpec(Base64.getDecoder().decode(receiptPublicKey))) as RSAPublicKey }.getOrNull()
    require(publicKey != null && publicKey.modulus.bitLength() >= 2048) { "Supply only the verifier RSA SPKI public key (base64), never private signing material" }
}
android {
    namespace = "com.lifetalea.app"
    compileSdk = 35
    ndkVersion = "28.2.13676358"
    defaultConfig {
        applicationId = "com.lifetalea.app"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        ndk { abiFilters += listOf("arm64-v8a", "armeabi-v7a") }
        externalNativeBuild { cmake { arguments += listOf("-DCMAKE_BUILD_TYPE=Release") } }
        buildConfigField("String", "RVS_URL", "\"$receiptUrl\"")
        buildConfigField("String", "RVS_PUBLIC_KEY", "\"$receiptPublicKey\"")
        buildConfigField("boolean", "AMAZON_PURCHASES_ENABLED", purchasesEnabled)
    }
    buildFeatures { compose = true; buildConfig = true }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
    buildTypes {
        debug { applicationIdSuffix = ".debug"; buildConfigField("String", "RVS_ENVIRONMENT", "\"$receiptEnvironment\"") }
        release { isMinifyEnabled = false; buildConfigField("String", "RVS_ENVIRONMENT", "\"production\"") }
        create("amazonTest") {
            initWith(getByName("release"))
            matchingFallbacks += listOf("release")
            // Same application ID for Amazon LAT; unsigned until Amazon processes the upload.
            // These public properties must be provided by build_amazon_test.py.
            buildConfigField("boolean", "AMAZON_PURCHASES_ENABLED", "true")
        }
        create("billingQa") {
            initWith(getByName("debug"))
            applicationIdSuffix = ".billingqa"
            signingConfig = signingConfigs.getByName("debug")
            matchingFallbacks += listOf("debug")
            buildConfigField("String", "RVS_URL", "\"https://localhost:8443/v1/verify\"")
            buildConfigField("String", "RVS_PUBLIC_KEY", "\"$billingQaPublicKey\"")
            buildConfigField("String", "RVS_ENVIRONMENT", "\"sandbox\"")
            buildConfigField("boolean", "AMAZON_PURCHASES_ENABLED", "true")
        }
    }
    externalNativeBuild { cmake { path = file("src/main/cpp/CMakeLists.txt"); version = "3.31.6" } }
    androidResources { noCompress += "bin" }
    sourceSets.getByName("main").assets.srcDir("build/generated/transcription/assets")
    sourceSets.getByName("billingQa").res.srcDir("build/generated/localBillingQa/res")
    packaging { resources.excludes += "/META-INF/{AL2.0,LGPL2.1}" }
    testOptions { unitTests.isReturnDefaultValues = true }
}
val prepareTranscriptionModel by tasks.registering {
    val model = layout.buildDirectory.file("generated/transcription/assets/transcription/ggml-tiny.bin")
    outputs.file(model)
    val expected = "be07e048e1e599ad46341c8d2a135645097a538221678b7acdd1b1919c6e1b21"
    inputs.property("sha256", expected)
    doLast {
        val target = model.get().asFile
        target.parentFile.mkdirs()
        val temporary = File(target.parentFile, "model.download")
        try {
            val connection = URI("https://huggingface.co/ggerganov/whisper.cpp/resolve/5359861c739e955e79d9a303bcbc70fb988958b1/ggml-tiny.bin").toURL().openConnection()
            connection.connectTimeout = 30000; connection.readTimeout = 60000
            val digest = MessageDigest.getInstance("SHA-256")
            var total = 0L
            connection.getInputStream().use { input -> temporary.outputStream().use { output ->
                val buffer = ByteArray(65536)
                while (true) {
                    val size = input.read(buffer); if (size < 0) break
                    total += size; check(total <= 77691713L) { "Unexpected transcription model size" }
                    digest.update(buffer, 0, size); output.write(buffer, 0, size)
                }
            } }
            check(total == 77691713L && digest.digest().joinToString("") { "%02x".format(it) } == expected) { "Transcription model checksum mismatch" }
            Files.move(temporary.toPath(), target.toPath(), StandardCopyOption.REPLACE_EXISTING)
        } finally { temporary.delete() }
    }
}
tasks.named("preBuild").configure { dependsOn(prepareTranscriptionModel) }
androidComponents {
    onVariants(selector().withBuildType("release")) { variant ->
        // Preserve the verified v5 upload; further product/localization changes use v6.
        variant.outputs.forEach { it.versionCode.set(6) }
    }
    onVariants(selector().withBuildType("amazonTest")) { variant ->
        variant.outputs.forEach { it.versionCode.set(6) }
    }
}
ksp { arg("room.schemaLocation", "$projectDir/schemas") }
dependencies {
    implementation(platform("androidx.compose:compose-bom:2025.04.01"))
    implementation("androidx.activity:activity-compose:1.10.1")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.compose.ui:ui-tooling-preview")
    debugImplementation("androidx.compose.ui:ui-tooling")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.7")
    implementation("androidx.room:room-runtime:2.7.1")
    implementation("androidx.room:room-ktx:2.7.1")
    ksp("androidx.room:room-compiler:2.7.1")
    implementation("androidx.datastore:datastore-preferences:1.1.4")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("io.coil-kt:coil-compose:2.7.0")
    implementation("com.amazon.device:amazon-appstore-sdk:3.0.9")
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test:runner:1.6.2")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.room:room-testing:2.7.1")
    androidTestImplementation(platform("androidx.compose:compose-bom:2025.04.01"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
