package com.lifetalea.app

import android.content.ContextWrapper
import android.graphics.Bitmap
import android.graphics.Color
import android.os.SystemClock
import androidx.room.Room
import androidx.room.withTransaction
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.lifetalea.app.data.*
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.*
import java.util.UUID

/** Fictional fixtures in separate QA databases/files; never opens the user's library. */
@RunWith(AndroidJUnit4::class)
class ScalePreservationTest {
    private val target get() = InstrumentationRegistry.getInstrumentation().targetContext
    private fun context(root: File) = object : ContextWrapper(target) { override fun getFilesDir() = root }

    @Test fun thousandMemoryArchivePreservesSelectedContentAcrossReopenAndInterruptedRead() = runBlocking {
        val root = File(target.cacheDir, "scale-${UUID.randomUUID()}").apply { mkdirs() }
        val name = "scale-${UUID.randomUUID()}.db"
        val sourceDb = Room.inMemoryDatabaseBuilder(target, LifeDatabase::class.java).build()
        var destinationDb = Room.databaseBuilder(target, LifeDatabase::class.java, name).build()
        try {
            val source = LibraryRepository(context(File(root, "source")), sourceDb)
            val memories = (0 until 1000).map { index ->
                Memory(title = "Fictional scale memory ${index.toString().padStart(4, '0')}",
                    story = "Fictional preservation fixture: café, 家族, أسرة. ".repeat(12),
                    transcript = "Fictional written transcript $index", date = (1950 + index % 75).toString(),
                    precision = "YEAR", location = "Fictional town", tags = "fictional, scale", favourite = index % 7 == 0)
            }
            val albums = (0 until 5).map { Album(title = "Fictional album $it") }
            val books = (0 until 5).map { Scrapbook(title = "Fictional book $it") }
            val photoBytes = ByteArrayOutputStream().also { out ->
                Bitmap.createBitmap(256, 256, Bitmap.Config.ARGB_8888).apply {
                    eraseColor(Color.rgb(56, 88, 74)); compress(Bitmap.CompressFormat.PNG, 100, out); recycle()
                }
            }.toByteArray()
            val audioBytes = ByteArray(16_384) { (it % 251).toByte() } // Byte-preservation fixture, not playable audio.
            sourceDb.withTransaction {
                albums.forEach { source.dao.save(it) }; books.forEach { source.dao.save(it) }
                memories.forEachIndexed { index, memory ->
                    source.dao.save(memory); source.dao.link(AlbumMemory(albums[index % albums.size].id, memory.id))
                    if (index % 10 == 0) {
                        val file = source.file("scale-$index.photo").apply { writeBytes(photoBytes) }
                        source.dao.save(Attachment(memoryId = memory.id, filename = file.name, kind = "photo", name = "Fictional photo $index"))
                    }
                    if (index % 50 == 0) {
                        val file = source.file("scale-$index.m4a").apply { writeBytes(audioBytes) }
                        source.dao.save(Attachment(memoryId = memory.id, filename = file.name, kind = "audio", name = "Binary fixture $index", durationMs = 1000))
                    }
                    if (index < 25) source.dao.save(BookPage(bookId = books[index % books.size].id, memoryId = memory.id,
                        position = index / books.size, caption = "Fictional caption $index"))
                }
            }
            val exportStart = SystemClock.elapsedRealtime()
            val bytes = BackupService(source).create(true, true, "fictional test passphrase".toCharArray())
            val exportMs = SystemClock.elapsedRealtime() - exportStart
            var destination = LibraryRepository(context(File(root, "destination")), destinationDb)
            val restoreStart = SystemClock.elapsedRealtime()
            val service = BackupService(destination)
            val archive = service.validate(ByteArrayInputStream(bytes), "fictional test passphrase".toCharArray())
            assertEquals(1000, archive.preview.memories); assertEquals(120, archive.preview.media); assertEquals(0, archive.preview.duplicates)
            service.restore(archive)
            val restoreMs = SystemClock.elapsedRealtime() - restoreStart
            destinationDb.close()
            destinationDb = Room.databaseBuilder(target, LifeDatabase::class.java, name).build()
            destination = LibraryRepository(context(File(root, "destination")), destinationDb)
            assertEquals(memories.toSet(), destination.dao.allMemories().toSet())
            assertEquals(albums.toSet(), destination.dao.allAlbums().toSet())
            assertEquals(source.dao.allLinks().toSet(), destination.dao.allLinks().toSet())
            assertEquals(books.toSet(), destination.dao.allBooks().toSet())
            fun pageContent(page: BookPage) = listOf(page.bookId, page.memoryId, page.position, page.caption, page.layout)
            assertEquals(source.dao.allPages().map(::pageContent).toSet(), destination.dao.allPages().map(::pageContent).toSet())
            val restoredMedia = destination.dao.allMedia()
            assertEquals(120, restoredMedia.size)
            restoredMedia.forEach { media -> assertArrayEquals(if (media.kind == "photo") photoBytes else audioBytes, destination.file(media.filename).readBytes()) }
            val duplicateService = BackupService(destination)
            val duplicate = duplicateService.validate(ByteArrayInputStream(bytes), "fictional test passphrase".toCharArray())
            assertEquals(1000, duplicate.preview.duplicates); duplicateService.restore(duplicate)
            assertEquals(1000, destination.dao.allMemories().size); assertEquals(restoredMedia.toSet(), destination.dao.allMedia().toSet())
            val interrupted = object : FilterInputStream(ByteArrayInputStream(bytes)) {
                private var readCount = 0
                override fun read(buffer: ByteArray, offset: Int, length: Int): Int {
                    if (readCount >= bytes.size / 2) throw IOException("Fictional interrupted document provider")
                    return super.read(buffer, offset, length).also { if (it > 0) readCount += it }
                }
            }
            try { duplicateService.validate(interrupted, "fictional test passphrase".toCharArray()); fail("Interrupted input accepted") } catch (_: IOException) { }
            assertEquals(memories.toSet(), destination.dao.allMemories().toSet())
            assertEquals(restoredMedia.toSet(), destination.dao.allMedia().toSet())
            val evidence = File(target.filesDir, "test-evidence").apply { mkdirs() }
            File(evidence, "scale-preservation.json").writeText(JSONObject().put("status", "PASS").put("memories", 1000)
                .put("albums", 5).put("photos", 100).put("binaryAudioFixtures", 20).put("books", 5).put("pages", 25)
                .put("encryptedArchiveBytes", bytes.size).put("exportMs", exportMs).put("validateAndRestoreMs", restoreMs)
                .put("scope", "Isolated fictional library within published archive limits; exact records/media, duplicate restore, interrupted input and database reopen. These timings are observations, not established UI performance budgets or process-death recovery.").toString(2))
        } finally { sourceDb.close(); destinationDb.close(); target.deleteDatabase(name); root.deleteRecursively() }
    }

    @Test fun oversizedSelectedAttachmentIsRejectedWithoutDroppingLibraryContent() = runBlocking {
        val root = File(target.cacheDir, "limit-${UUID.randomUUID()}").apply { mkdirs() }
        val db = Room.inMemoryDatabaseBuilder(target, LifeDatabase::class.java).build()
        try {
            val repo = LibraryRepository(context(root), db)
            val memory = Memory(title = "Fictional oversized media check")
            repo.dao.save(memory)
            val file = repo.file("oversized.m4a")
            RandomAccessFile(file, "rw").use { it.setLength(BackupService.MAX_ITEM.toLong() + 1) }
            val attachment = Attachment(memoryId = memory.id, filename = file.name, kind = "audio", name = "Sparse size fixture")
            repo.dao.save(attachment)
            try { BackupService(repo).create(false, true); fail("Oversized selected attachment silently omitted") } catch (_: IllegalArgumentException) { }
            assertEquals(listOf(memory), repo.dao.allMemories()); assertEquals(listOf(attachment), repo.dao.allMedia())
            assertEquals(BackupService.MAX_ITEM.toLong() + 1, file.length())
        } finally { db.close(); root.deleteRecursively() }
    }
}
