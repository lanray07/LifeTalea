package com.lifetalea.app.voice

import android.media.AudioFormat
import android.media.MediaCodec
import android.media.MediaExtractor
import android.media.MediaFormat
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.abs

/** Decodes the saved file, never the microphone or a recognition-service intent. */
internal object RecordedAudio {
    const val MAX_SECONDS = 600
    const val RATE = 16000
    fun decode(file: File, cancelled: () -> Boolean): FloatArray {
        require(file.isFile && file.length() in 1..(200L * 1024 * 1024))
        val extractor = MediaExtractor()
        var codec: MediaCodec? = null
        try {
            extractor.setDataSource(file.path)
            val track = (0 until extractor.trackCount).firstOrNull {
                extractor.getTrackFormat(it).getString(MediaFormat.KEY_MIME)?.startsWith("audio/") == true
            } ?: error("No audio track")
            extractor.selectTrack(track)
            val format = extractor.getTrackFormat(track)
            if (format.containsKey(MediaFormat.KEY_DURATION))
                require(format.getLong(MediaFormat.KEY_DURATION) <= MAX_SECONDS * 1000000L) { "transcription_limit" }
            val pcm = PcmCollector(format)
            val mime = requireNotNull(format.getString(MediaFormat.KEY_MIME))
            if (mime == "audio/raw") {
                val buffer = ByteBuffer.allocate(65536)
                while (!cancelled()) {
                    buffer.clear()
                    val size = extractor.readSampleData(buffer, 0)
                    if (size < 0) break
                    buffer.position(0); buffer.limit(size); pcm.accept(buffer)
                    extractor.advance()
                }
            } else {
                val decoder = MediaCodec.createDecoderByType(mime); codec = decoder
                decoder.configure(format, null, null, 0); decoder.start()
                var inputDone = false; var outputDone = false
                val info = MediaCodec.BufferInfo()
                var lastOutput = android.os.SystemClock.elapsedRealtime()
                while (!outputDone && !cancelled()) {
                    check(android.os.SystemClock.elapsedRealtime() - lastOutput < 30000) { "Decoder stalled" }
                    if (!inputDone) {
                        val index = decoder.dequeueInputBuffer(10000)
                        if (index >= 0) {
                            val buffer = requireNotNull(decoder.getInputBuffer(index)); buffer.clear()
                            val size = extractor.readSampleData(buffer, 0)
                            if (size < 0) {
                                decoder.queueInputBuffer(index, 0, 0, 0, MediaCodec.BUFFER_FLAG_END_OF_STREAM); inputDone = true
                            } else {
                                decoder.queueInputBuffer(index, 0, size, extractor.sampleTime, 0); extractor.advance()
                            }
                        }
                    }
                    val index = decoder.dequeueOutputBuffer(info, 10000)
                    if (index == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED) pcm.configure(decoder.outputFormat)
                    if (index >= 0) {
                        lastOutput = android.os.SystemClock.elapsedRealtime()
                        try {
                            if (info.size > 0) {
                                val buffer = requireNotNull(decoder.getOutputBuffer(index))
                                buffer.position(info.offset); buffer.limit(info.offset + info.size); pcm.accept(buffer)
                            }
                            outputDone = info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0
                        } finally { decoder.releaseOutputBuffer(index, false) }
                    }
                }
            }
            check(!cancelled()) { "Cancelled" }
            return pcm.result()
        } finally { runCatching { codec?.stop() }; codec?.release(); extractor.release() }
    }

    private class PcmCollector(format: MediaFormat) {
        private var rate = 0; private var channels = 0; private var encoding = AudioFormat.ENCODING_PCM_16BIT
        private var sourceIndex = 0L; private var nextOutput = 0.0; private var previous = 0f
        private var values = FloatArray(RATE); private var count = 0
        init { configure(format) }
        fun configure(format: MediaFormat) {
            val newRate = format.getInteger(MediaFormat.KEY_SAMPLE_RATE)
            val newChannels = format.getInteger(MediaFormat.KEY_CHANNEL_COUNT)
            require(newRate in 8000..192000 && newChannels in 1..8)
            require(sourceIndex == 0L || (newRate == rate && newChannels == channels))
            rate = newRate; channels = newChannels
            encoding = if (format.containsKey(MediaFormat.KEY_PCM_ENCODING)) format.getInteger(MediaFormat.KEY_PCM_ENCODING) else AudioFormat.ENCODING_PCM_16BIT
            require(encoding == AudioFormat.ENCODING_PCM_16BIT || encoding == AudioFormat.ENCODING_PCM_FLOAT)
        }
        fun accept(buffer: ByteBuffer) {
            buffer.order(ByteOrder.LITTLE_ENDIAN)
            val frameBytes = channels * if (encoding == AudioFormat.ENCODING_PCM_FLOAT) 4 else 2
            require(buffer.remaining() % frameBytes == 0)
            while (buffer.remaining() >= frameBytes) {
                var sample = 0f
                repeat(channels) {
                    val value = if (encoding == AudioFormat.ENCODING_PCM_FLOAT) buffer.float else buffer.short / 32768f
                    require(value.isFinite()); sample += value.coerceIn(-1f, 1f) / channels
                }
                while (nextOutput <= sourceIndex.toDouble()) {
                    require(count < RATE * MAX_SECONDS) { "transcription_limit" }
                    if (count == values.size) values = values.copyOf((values.size * 2).coerceAtMost(RATE * MAX_SECONDS))
                    val mix = (nextOutput - (sourceIndex - 1)).toFloat().coerceIn(0f, 1f)
                    values[count++] = if (sourceIndex == 0L) sample else previous + (sample - previous) * mix
                    nextOutput += rate.toDouble() / RATE
                }
                previous = sample; sourceIndex++
            }
        }
        fun result(): FloatArray { require(count >= RATE / 2); return values.copyOf(count) }
    }
}
