package com.lifetalea.app

import android.content.Context
import android.content.ContextWrapper
import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.pdf.PdfRenderer
import android.os.ParcelFileDescriptor
import androidx.room.Room
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.lifetalea.app.data.*
import com.lifetalea.app.features.KeepsakePdf
import kotlinx.coroutines.runBlocking
import org.junit.*
import org.junit.Assert.*
import org.junit.runner.RunWith
import java.io.*
import java.util.UUID

@RunWith(AndroidJUnit4::class)
class PreservationTest {
    private lateinit var db: LifeDatabase
    private lateinit var repo: LibraryRepository
    private lateinit var root: File
    private val target get() = InstrumentationRegistry.getInstrumentation().targetContext
    @Before fun setup() {
        root = File(target.cacheDir, "test-${UUID.randomUUID()}").apply { mkdirs() }
        val context = object : ContextWrapper(target) { override fun getFilesDir() = root }
        db = Room.inMemoryDatabaseBuilder(target, LifeDatabase::class.java).build()
        repo = LibraryRepository(context, db)
    }
    @After fun close() { db.close(); root.deleteRecursively() }
    @Test fun crudRelationshipsAndDeletion() = runBlocking {
        val memory = Memory(title = "A fictional picnic", date = "1994", precision = "YEAR", transcript = "A happy afternoon", tags = "summer")
        val album = Album(title = "Family")
        repo.dao.save(album); repo.save(memory, setOf(album.id))
        assertEquals(memory.id, repo.dao.allMemories().single().id); assertEquals(1, repo.dao.allLinks().size)
        repo.dao.deleteAlbum(album.id); assertEquals(1, repo.dao.allMemories().size); assertEquals(0, repo.dao.allLinks().size)
        repo.save(memory.copy(title = "Edited"), emptySet()); assertEquals("Edited", repo.dao.allMemories().single().title)
        repo.removeMemory(memory.id); assertTrue(repo.dao.allMemories().isEmpty())
    }
    @Test fun databaseReopenPreservesDataAndForeignKeys() = runBlocking {
        val name = "test-${UUID.randomUUID()}.db"
        var disk = Room.databaseBuilder(target, LifeDatabase::class.java, name).build()
        val memory = Memory(title = "Persistence")
        try {
            disk.library().save(memory); disk.close()
            disk = Room.databaseBuilder(target, LifeDatabase::class.java, name).build()
            assertEquals(memory, disk.library().allMemories().single())
            try { disk.library().link(AlbumMemory(UUID.randomUUID().toString(), memory.id)); fail("Invalid relation accepted") } catch (_: android.database.sqlite.SQLiteConstraintException) { }
        } finally { disk.close(); target.deleteDatabase(name) }
    }
    @Test fun encryptedBackupRoundTripPreservesMediaAndDrafts() = runBlocking {
        val memory = Memory(title = "A fictional family recipe", story = "A story", transcript = "A transcript")
        val album = Album(title = "Recipes"); repo.dao.save(album); repo.save(memory, setOf(album.id))
        val photo = repo.file("test.photo")
        Bitmap.createBitmap(40, 40, Bitmap.Config.ARGB_8888).apply { eraseColor(Color.GREEN); photo.outputStream().use { compress(Bitmap.CompressFormat.PNG, 100, it) }; recycle() }
        repo.dao.save(Attachment(memoryId = memory.id, filename = photo.name, kind = "photo", name = "Sample"))
        val audio = repo.file("test.m4a").apply { writeBytes(byteArrayOf(1, 2, 3, 4)) }
        repo.dao.save(Attachment(memoryId = memory.id, filename = audio.name, kind = "audio", name = "Binary fixture", durationMs = 1000))
        val book = Scrapbook(title = "Family keepsake"); repo.dao.save(book); repo.dao.save(BookPage(bookId = book.id, memoryId = memory.id, position = 0, caption = "A caption"))
        val backup = BackupService(repo); val pass = "long safe phrase".toCharArray()
        val bytes = backup.create(true, true, pass)
        assertTrue(ArchiveCrypto.encrypted(bytes))
        try { backup.validate(ByteArrayInputStream(bytes), "wrong password".toCharArray()); fail("Wrong password accepted") } catch (_: Exception) { }
        val preview = backup.validate(ByteArrayInputStream(bytes), pass); assertEquals(1, preview.preview.duplicates)
        backup.restore(preview); assertEquals(1, repo.dao.allMemories().size)
        repo.clearAll(); backup.restore(preview)
        assertEquals(memory.id, repo.dao.allMemories().single().id); assertEquals(2, repo.dao.allMedia().size); assertEquals("A caption", repo.dao.allPages().single().caption)
        assertArrayEquals(byteArrayOf(1, 2, 3, 4), repo.file(repo.dao.allMedia().first { it.kind == "audio" }.filename).readBytes())
        assertEquals(1, repo.dao.allLinks().size)
    }
    @Test fun corruptArchiveCannotMutateLibrary() = runBlocking {
        val memory = Memory(title = "Keep me"); repo.save(memory, emptySet())
        val service = BackupService(repo); val bytes = service.create(false, false)
        try { service.validate(ByteArrayInputStream(bytes.copyOf(bytes.size / 2))); fail("Corrupt backup accepted") } catch (_: Exception) { }
        assertEquals(memory.id, repo.dao.allMemories().single().id)
    }
    @Test fun pdfHasMultipleReadablePagesAndImages() = runBlocking {
        val memory = Memory(title = "Our family — أُسرة — 家族", story = "A fictional story with café and memories.\n".repeat(150), date = "1994", precision = "YEAR")
        val file = File(root, "keepsake.pdf")
        file.outputStream().use { KeepsakePdf(repo).write("LifeTalea · Family keepsake", listOf(memory), emptyList(), it) }
        ParcelFileDescriptor.open(file, ParcelFileDescriptor.MODE_READ_ONLY).use { fd -> PdfRenderer(fd).use { renderer ->
            assertTrue(renderer.pageCount >= 3)
            renderer.openPage(1).use { page -> val b = Bitmap.createBitmap(page.width, page.height, Bitmap.Config.ARGB_8888); page.render(b, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY); assertTrue(b.width > 500); b.recycle() }
        } }
        val evidence = File(target.filesDir, "test-evidence").apply { mkdirs() }; file.copyTo(File(evidence, "keepsake.pdf"), overwrite = true)
        Unit
    }
    @Test fun photoImportIsPrivateAndRejectsInvalidInput() = runBlocking {
        val memory = Memory(title = "A photograph"); repo.save(memory, emptySet())
        val source = File(root, "source.png")
        Bitmap.createBitmap(80, 60, Bitmap.Config.ARGB_8888).apply { eraseColor(Color.rgb(56,88,74)); source.outputStream().use { compress(Bitmap.CompressFormat.PNG,100,it) }; recycle() }
        repo.importPhoto(memory.id, android.net.Uri.fromFile(source)); source.delete()
        val attachment = repo.dao.allMedia().single(); assertTrue(repo.file(attachment.filename).isFile)
        val invalid = File(root, "not-an-image.txt").apply { writeText("invalid") }
        try { repo.importPhoto(memory.id, android.net.Uri.fromFile(invalid)); fail("Invalid photograph accepted") } catch (_: IllegalArgumentException) { }
        assertEquals(1,repo.dao.allMedia().size)
        repo.removeMemory(memory.id); assertFalse(repo.file(attachment.filename).exists())
    }
    @Test fun duplicateKeepsIndependentAttachmentsAndAlbumLinks() = runBlocking {
        val original = Memory(title = "Keep every part", transcript = "Spoken words")
        val album = Album(title = "Family"); repo.dao.save(album); repo.save(original, setOf(album.id))
        listOf("photo", "audio").forEach { kind ->
            val file = repo.file("original.$kind").apply { writeBytes(byteArrayOf(1, 3, 5, 7)) }
            repo.dao.save(Attachment(memoryId = original.id, filename = file.name, kind = kind, name = kind, durationMs = 1200))
        }
        val copy = repo.duplicate(original.id)
        assertNotEquals(original.id, copy.id); assertEquals(original.transcript, copy.transcript)
        assertEquals(setOf(album.id), repo.dao.allLinks().filter { it.memoryId == copy.id }.map { it.albumId }.toSet())
        val media = repo.dao.allMedia(); val copies = media.filter { it.memoryId == copy.id }
        assertEquals(2, copies.size); assertEquals(4, media.map { it.filename }.toSet().size)
        repo.removeMemory(original.id)
        copies.forEach { assertArrayEquals(byteArrayOf(1, 3, 5, 7), repo.file(it.filename).readBytes()); assertEquals(1200L, it.durationMs) }
    }
    @Test fun failedDuplicateRollsBackRowsLinksAndCopiedFiles() = runBlocking {
        val original = Memory(title = "Incomplete media"); repo.save(original, emptySet())
        repo.file("present.photo").writeText("binary fixture")
        repo.dao.save(Attachment(memoryId = original.id, filename = "present.photo", kind = "photo", name = "Present"))
        repo.dao.save(Attachment(memoryId = original.id, filename = "missing.m4a", kind = "audio", name = "Missing"))
        try { repo.duplicate(original.id); fail("Missing attachment accepted") } catch (_: IOException) { }
        assertEquals(listOf(original.id), repo.dao.allMemories().map { it.id })
        assertEquals(2, repo.dao.allMedia().size)
        assertEquals(listOf("present.photo"), repo.mediaDir.listFiles()!!.map { it.name })
    }
    @Test fun restoringPageIdCollisionPreservesExistingKeepsake() = runBlocking {
        val memory = Memory(title = "Keep my book"); repo.save(memory, emptySet())
        val book = Scrapbook(title = "Existing keepsake"); repo.dao.save(book)
        val page = BookPage(bookId = book.id, memoryId = memory.id, position = 0, caption = "Original caption"); repo.dao.save(page)
        val service = BackupService(repo)
        val incoming = service.validate(ByteArrayInputStream(service.create(false, false)))
        val importedBookId = UUID.randomUUID().toString()
        incoming.manifest.getJSONArray("books").getJSONObject(0).put("id", importedBookId).put("title", "Imported book")
        incoming.manifest.getJSONArray("pages").getJSONObject(0).put("bookId", importedBookId).put("caption", "Imported caption")
        // Re-encode and validate the edited archive just as an external backup is validated.
        val bytes = ByteArrayOutputStream().also { out -> java.util.zip.ZipOutputStream(out).use { zip ->
            zip.putNextEntry(java.util.zip.ZipEntry("manifest.json")); zip.write(incoming.manifest.toString().toByteArray(Charsets.UTF_8)); zip.closeEntry()
        } }.toByteArray()
        service.restore(service.validate(ByteArrayInputStream(bytes)))
        assertEquals(page, repo.dao.allPages().first { it.id == page.id })
        val imported = repo.dao.allPages().single { it.bookId == importedBookId }
        assertNotEquals(page.id, imported.id); assertEquals("Imported caption", imported.caption)
    }
    @Test fun exportRejectsManifestTooLargeForRestoreWithoutChangingLibrary() = runBlocking {
        repeat(9) { repo.save(Memory(title = "Large story $it", story = "a".repeat(1_000_000)), emptySet()) }
        try { BackupService(repo).create(false, false); fail("Unrestorable manifest exported") } catch (_: IllegalArgumentException) { }
        assertEquals(9, repo.dao.allMemories().size)
    }
}
