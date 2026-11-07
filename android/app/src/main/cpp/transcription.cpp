#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <atomic>
#include <algorithm>
#include <memory>
#include <string>
#include <thread>
#include "whisper.h"

struct Task { std::atomic<bool> cancelled{false}; std::atomic<int> progress{0}; };
static Task * task(jlong id) { return reinterpret_cast<Task *>(id); }
static void fail(JNIEnv * env, const char * text) {
    env->ThrowNew(env->FindClass("java/lang/IllegalStateException"), text);
}
extern "C" JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM *, void *) {
    // Neither audio, recognized words nor model internals belong in device logs.
    whisper_log_set([](enum ggml_log_level, const char *, void *) {}, nullptr);
    return JNI_VERSION_1_6;
}
extern "C" JNIEXPORT jlong JNICALL
Java_com_lifetalea_app_voice_WhisperNative_createTask(JNIEnv *, jobject) { return reinterpret_cast<jlong>(new Task()); }
extern "C" JNIEXPORT void JNICALL
Java_com_lifetalea_app_voice_WhisperNative_cancel(JNIEnv *, jobject, jlong id) { task(id)->cancelled.store(true); }
extern "C" JNIEXPORT jint JNICALL
Java_com_lifetalea_app_voice_WhisperNative_progress(JNIEnv *, jobject, jlong id) { return task(id)->progress.load(); }
extern "C" JNIEXPORT void JNICALL
Java_com_lifetalea_app_voice_WhisperNative_release(JNIEnv *, jobject, jlong id) { delete task(id); }

extern "C" JNIEXPORT jbyteArray JNICALL
Java_com_lifetalea_app_voice_WhisperNative_transcribe(JNIEnv * env, jobject, jobject assets,
                                                    jfloatArray samples, jstring language, jlong id) {
    Task * work = task(id);
    if (work->cancelled.load()) return nullptr;
    const char * lang = env->GetStringUTFChars(language, nullptr);
    std::string selected(lang); env->ReleaseStringUTFChars(language, lang);
    if (whisper_lang_id(selected.c_str()) < 0) { fail(env, "Unsupported transcription language"); return nullptr; }
    AAsset * asset = AAssetManager_open(AAssetManager_fromJava(env, assets), "transcription/ggml-tiny.bin", AASSET_MODE_RANDOM);
    if (!asset) { fail(env, "Transcription model unavailable"); return nullptr; }
    whisper_model_loader loader{};
    loader.context = asset;
    loader.read = [](void * ctx, void * out, size_t size) -> size_t {
        auto n = AAsset_read(static_cast<AAsset *>(ctx), out, size);
        return n > 0 ? static_cast<size_t>(n) : 0;
    };
    loader.eof = [](void * ctx) { return AAsset_getRemainingLength64(static_cast<AAsset *>(ctx)) == 0; };
    loader.close = [](void * ctx) { AAsset_close(static_cast<AAsset *>(ctx)); };
    auto options = whisper_context_default_params(); options.use_gpu = false;
    std::unique_ptr<whisper_context, decltype(&whisper_free)> ctx(whisper_init_with_params(&loader, options), whisper_free);
    if (!ctx) { fail(env, "Transcription model could not be loaded"); return nullptr; }
    if (work->cancelled.load()) return nullptr;
    const auto length = env->GetArrayLength(samples);
    if (length <= 0 || length > 16000 * 600) { fail(env, "Recording length exceeds transcription limit"); return nullptr; }
    float * pcm = env->GetFloatArrayElements(samples, nullptr);
    if (!pcm) return nullptr;
    auto params = whisper_full_default_params(WHISPER_SAMPLING_GREEDY);
    params.n_threads = std::max(1u, std::min(4u, std::thread::hardware_concurrency()));
    params.language = selected.c_str(); params.translate = false; params.no_context = true;
    params.print_realtime = params.print_progress = params.print_timestamps = params.print_special = false;
    params.suppress_nst = true; params.temperature = 0.0f; params.temperature_inc = 0.0f;
    params.abort_callback = [](void * user) { return static_cast<Task *>(user)->cancelled.load(); };
    params.abort_callback_user_data = work;
    params.progress_callback = [](whisper_context *, whisper_state *, int percent, void * user) {
        static_cast<Task *>(user)->progress.store(percent);
    };
    params.progress_callback_user_data = work;
    int status = whisper_full(ctx.get(), params, pcm, length);
    env->ReleaseFloatArrayElements(samples, pcm, JNI_ABORT);
    if (work->cancelled.load()) return nullptr;
    if (status != 0) { fail(env, "Transcription failed"); return nullptr; }
    std::string text;
    for (int i = 0; i < whisper_full_n_segments(ctx.get()); ++i) {
        if (whisper_full_get_segment_no_speech_prob(ctx.get(), i) > 0.6f) continue;
        text += whisper_full_get_segment_text(ctx.get(), i);
    }
    if (text.size() > 1000000) { fail(env, "Transcript exceeds text limit"); return nullptr; }
    auto result = env->NewByteArray(static_cast<jsize>(text.size()));
    if (result) env->SetByteArrayRegion(result, 0, static_cast<jsize>(text.size()), reinterpret_cast<const jbyte *>(text.data()));
    return result;
}
