package com.lifetalea.app.features

import android.graphics.*
import android.graphics.pdf.PdfDocument
import android.text.Layout
import android.text.StaticLayout
import android.text.TextPaint
import com.lifetalea.app.data.*
import java.io.OutputStream

class KeepsakePdf(private val repo: LibraryRepository) {
    fun write(title: String, memories: List<Memory>, media: List<Attachment>, out: OutputStream, includeLocation: Boolean = false, includeTranscript: Boolean = false, letter: Boolean = false) {
        require(memories.isNotEmpty())
        val width = if (letter) 612 else 595; val height = if (letter) 792 else 842
        val paint = TextPaint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.rgb(48, 47, 45); textSize = 12f }
        val footerPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.rgb(48, 47, 45); textSize = 10f }
        val pdf = PdfDocument()
        try {
            var pageNo = 0
            fun page(): PdfDocument.Page {
                pageNo++
                return pdf.startPage(PdfDocument.PageInfo.Builder(width, height, pageNo).create()).also {
                    it.canvas.drawColor(Color.WHITE)
                    it.canvas.drawText(pageNo.toString(), width / 2f, height - 25f, footerPaint)
                }
            }
            var page = page(); paint.textSize = 32f; paint.typeface = Typeface.create("serif", Typeface.NORMAL)
            val cover = StaticLayout.Builder.obtain(title, 0, title.length, paint, width - 96).setAlignment(Layout.Alignment.ALIGN_CENTER).build()
            page.canvas.save(); page.canvas.translate(48f, height * .34f); cover.draw(page.canvas); page.canvas.restore(); pdf.finishPage(page)
            memories.forEach { memory ->
                page = page(); var y = 48f
                fun text(value: String, size: Float) {
                    paint.textSize = size
                    val layout = StaticLayout.Builder.obtain(value, 0, value.length, paint, width - 96).build()
                    // Render one line at a time so long stories continue onto new pages.
                    for (line in 0 until layout.lineCount) {
                        val top = layout.getLineTop(line); val bottom = layout.getLineBottom(line); val lineHeight = bottom - top
                        if (y + lineHeight > height - 55) { pdf.finishPage(page); page = page(); y = 48f }
                        page.canvas.save(); page.canvas.clipRect(48f, y, width - 48f, y + lineHeight)
                        page.canvas.translate(48f, y - top); layout.draw(page.canvas); page.canvas.restore(); y += lineHeight
                    }
                    y += 12
                }
                paint.typeface = Typeface.create("serif", Typeface.NORMAL); text(memory.title, 24f)
                paint.typeface = Typeface.create("sans-serif", Typeface.NORMAL)
                if (memory.date.isNotBlank()) text(memory.date, 11f)
                media.firstOrNull { it.memoryId == memory.id && it.kind == "photo" }?.let { a ->
                    val opts = BitmapFactory.Options().apply { inJustDecodeBounds = true }; val f = repo.file(a.filename)
                    BitmapFactory.decodeFile(f.path, opts); var sample = 1
                    while (opts.outWidth / sample > 1400 || opts.outHeight / sample > 1400) sample *= 2
                    val bitmap = BitmapFactory.decodeFile(f.path, BitmapFactory.Options().apply { inSampleSize = sample })
                    bitmap?.let { b ->
                        val scale = minOf((width - 96f) / b.width, 240f / b.height); val h = b.height * scale
                        if (y + h > height - 55) { pdf.finishPage(page); page = page(); y = 48f }
                        page.canvas.drawBitmap(b, null, RectF(48f, y, 48f + b.width * scale, y + h), null); y += h + 18; b.recycle()
                    }
                }
                text(memory.story, 12f)
                if (includeTranscript && memory.transcript.isNotBlank()) text(memory.transcript, 12f)
                if (includeLocation && memory.location.isNotBlank()) text(memory.location, 10f)
                pdf.finishPage(page)
            }
            pdf.writeTo(out)
        } finally { pdf.close() }
    }
}
