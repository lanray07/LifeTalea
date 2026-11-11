package com.lifetalea.app.data

import androidx.room.withTransaction
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.*
import java.security.MessageDigest
import java.security.SecureRandom
import java.util.UUID
import java.util.zip.*
import javax.crypto.Cipher
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.PBEKeySpec
import javax.crypto.spec.SecretKeySpec

object ArchiveCrypto {
    private val magic = "LTALEA01".toByteArray()
    fun encrypted(bytes: ByteArray) = bytes.size >= 8 && bytes.copyOfRange(0, 8).contentEquals(magic)
    private fun key(password: CharArray, salt: ByteArray) = SecretKeySpec(SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(PBEKeySpec(password, salt, 210000, 256)).encoded, "AES")
    fun encrypt(bytes: ByteArray, password: CharArray): ByteArray {
        require(password.size >= 10)
        val salt = ByteArray(16).also { SecureRandom().nextBytes(it) }; val iv = ByteArray(12).also { SecureRandom().nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding"); cipher.init(Cipher.ENCRYPT_MODE, key(password, salt), GCMParameterSpec(128, iv)); cipher.updateAAD(magic)
        return magic + salt + iv + cipher.doFinal(bytes)
    }
    fun decrypt(bytes: ByteArray, password: CharArray): ByteArray {
        require(bytes.size >= 52 && encrypted(bytes))
        val cipher = Cipher.getInstance("AES/GCM/NoPadding"); cipher.init(Cipher.DECRYPT_MODE, key(password, bytes.copyOfRange(8, 24)), GCMParameterSpec(128, bytes.copyOfRange(24, 36))); cipher.updateAAD(magic)
        return cipher.doFinal(bytes.copyOfRange(36, bytes.size))
    }
}

data class RestorePreview(val memories: Int, val albums: Int, val media: Int, val books: Int, val duplicates: Int)
data class ValidatedArchive(val manifest: JSONObject, val files: Map<String, ByteArray>, val preview: RestorePreview)
class BackupService(private val repo: LibraryRepository) {
    // Keep bounded working copies within tablet heaps. Larger libraries need a streaming format.
    companion object { const val MAX_ARCHIVE = 32 * 1024 * 1024; const val MAX_ITEM = 16 * 1024 * 1024; const val MAX_MANIFEST = 8 * 1024 * 1024 }
    private fun hash(bytes: ByteArray) = MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }
    private fun <T> array(items: List<T>, transform: (T) -> JSONObject): JSONArray {
        require(items.size <= BackupManifest.MAX_RECORDS)
        return JSONArray().also { a -> items.forEach { a.put(transform(it)) } }
    }
    suspend fun create(includePhotos: Boolean, includeAudio: Boolean, password: CharArray = charArrayOf()): ByteArray = withContext(Dispatchers.IO) {
        val dao = repo.dao
        val manifest = JSONObject().put("format", "lifetalea").put("version", 1)
        val blobs = linkedMapOf<String, ByteArray>()
        repo.db.withTransaction {
            manifest.put("memories", array(dao.allMemories()) { m -> JSONObject().put("id", m.id).put("title", m.title).put("story", m.story).put("date", m.date).put("precision", m.precision).put("location", m.location).put("tags", m.tags).put("transcript", m.transcript).put("favourite", m.favourite).put("createdAt", m.createdAt).put("updatedAt", m.updatedAt) })
            manifest.put("albums", array(dao.allAlbums()) { JSONObject().put("id", it.id).put("title", it.title).put("theme", it.theme) })
            manifest.put("links", array(dao.allLinks()) { JSONObject().put("albumId", it.albumId).put("memoryId", it.memoryId) })
            manifest.put("books", array(dao.allBooks()) { JSONObject().put("id", it.id).put("title", it.title).put("theme", it.theme).put("updatedAt", it.updatedAt) })
            manifest.put("pages", array(dao.allPages()) { JSONObject().put("id", it.id).put("bookId", it.bookId).put("memoryId", it.memoryId).put("position", it.position).put("caption", it.caption).put("layout", it.layout) })
            manifest.put("media", array(dao.allMedia().filter { (it.kind == "photo" && includePhotos) || (it.kind == "audio" && includeAudio) }) {
                val f = repo.file(it.filename); require(f.isFile && f.length() <= MAX_ITEM)
                val bytes = f.readBytes(); blobs[it.filename] = bytes
                require(blobs.values.sumOf { b -> b.size.toLong() } <= MAX_ARCHIVE - MAX_ITEM)
                JSONObject().put("id", it.id).put("memoryId", it.memoryId).put("filename", it.filename).put("kind", it.kind).put("name", it.name).put("durationMs", it.durationMs).put("sha256", hash(bytes))
            })
        }
        // Never export an archive that our own importer will refuse.
        val manifestBytes = manifest.toString().toByteArray(Charsets.UTF_8)
        require(manifestBytes.size <= MAX_MANIFEST)
        val result = ByteArrayOutputStream().also { buffer -> ZipOutputStream(buffer).use { zip ->
            zip.putNextEntry(ZipEntry("manifest.json")); zip.write(manifestBytes); zip.closeEntry()
            blobs.forEach { (name, bytes) -> zip.putNextEntry(ZipEntry("media/$name")); zip.write(bytes); zip.closeEntry() }
        } }.toByteArray()
        require(result.size <= MAX_ARCHIVE - if (password.isNotEmpty()) 52 else 0)
        if (password.isNotEmpty()) ArchiveCrypto.encrypt(result, password) else result
    }
    private fun objects(m: JSONObject, key: String): List<JSONObject> = m.getJSONArray(key).let { a -> require(a.length() <= BackupManifest.MAX_RECORDS); (0 until a.length()).map { a.getJSONObject(it) } }
    suspend fun validate(input: InputStream, password: CharArray = charArrayOf()): ValidatedArchive = withContext(Dispatchers.IO) {
        val raw = input.use { readLimited(it, MAX_ARCHIVE) }
        val bytes = if (ArchiveCrypto.encrypted(raw)) ArchiveCrypto.decrypt(raw, password) else raw
        val entries = linkedMapOf<String, ByteArray>()
        var manifest: JSONObject? = null
        var size = 0
        ZipInputStream(ByteArrayInputStream(bytes)).use { zip ->
            while (true) {
                val entry = zip.nextEntry ?: break
                require(!entry.isDirectory)
                require(entry.name == "manifest.json" || entry.name.matches(Regex("media/[a-zA-Z0-9._-]{1,100}")))
                if (entry.name == "manifest.json") {
                    require(manifest == null)
                    val manifestEntry = ManifestEntry(zip, minOf(MAX_MANIFEST, MAX_ARCHIVE - size))
                    manifest = BackupManifest.read(manifestEntry)
                    size += manifestEntry.count
                } else {
                    require(entries.size < BackupManifest.MAX_RECORDS && !entries.containsKey(entry.name))
                    val data = readLimited(zip, minOf(MAX_ITEM, MAX_ARCHIVE - size))
                    size += data.size
                    entries[entry.name] = data
                }
            }
        }
        val validatedManifest = requireNotNull(manifest) { "No manifest" }
        val memories = objects(validatedManifest, "memories"); val albums = objects(validatedManifest, "albums"); val media = objects(validatedManifest, "media"); val books = objects(validatedManifest, "books"); val pages = objects(validatedManifest, "pages"); val links = objects(validatedManifest, "links")
        fun ids(items: List<JSONObject>): Set<String> = items.map { it.getString("id").also { id -> require(UUID.fromString(id).toString() == id) } }.toSet().also { require(it.size == items.size) }
        val memoryIds = ids(memories); val albumIds = ids(albums); val bookIds = ids(books); ids(media); ids(pages)
        memories.forEach { require(it.getString("title").isNotBlank() && it.getString("title").length <= 300); require(MemoryRules.validDate(it.getString("date"), it.getString("precision"))); require(it.getString("story").length <= 1000000 && it.getString("transcript").length <= 1000000) }
        links.forEach { require(it.getString("albumId") in albumIds && it.getString("memoryId") in memoryIds) }
        pages.forEach { require(it.getString("bookId") in bookIds && it.getInt("position") >= 0); UUID.fromString(it.getString("memoryId")) }
        media.forEach {
            require(it.getString("memoryId") in memoryIds && it.getString("kind") in listOf("photo", "audio"))
            repo.file(it.getString("filename"))
            require(hash(entries["media/${it.getString("filename")}"] ?: error("Missing attachment")) == it.getString("sha256"))
        }
        require(entries.size == media.size && media.map { it.getString("filename") }.toSet().size == media.size)
        val existing = repo.dao.allMemories().map { it.id }.toSet()
        ValidatedArchive(validatedManifest, entries, RestorePreview(memories.size, albums.size, media.size, books.size, memoryIds.count { it in existing }))
    }
    // Conflict policy: keep existing records. All imports are validated before any mutation.
    suspend fun restore(archive: ValidatedArchive) = withContext(Dispatchers.IO) {
        val m = archive.manifest; val dao = repo.dao; val createdFiles = mutableListOf<File>()
        try {
            repo.db.withTransaction {
                val existingMemories = dao.allMemories().map { it.id }.toSet(); val existingAlbums = dao.allAlbums().map { it.id }.toSet(); val existingBooks = dao.allBooks().map { it.id }.toSet()
                objects(m, "memories").filter { it.getString("id") !in existingMemories }.forEach { x -> dao.save(Memory(x.getString("id"), x.getString("title"), x.getString("story"), x.getString("date"), x.getString("precision"), x.getString("location"), x.getString("tags"), x.getString("transcript"), x.getBoolean("favourite"), x.getLong("createdAt"), x.getLong("updatedAt"))) }
                objects(m, "albums").filter { it.getString("id") !in existingAlbums }.forEach { dao.save(Album(it.getString("id"), it.getString("title"), it.getString("theme"))) }
                objects(m, "links").filter { it.getString("memoryId") !in existingMemories }.forEach { dao.link(AlbumMemory(it.getString("albumId"), it.getString("memoryId"))) }
                objects(m, "books").filter { it.getString("id") !in existingBooks }.forEach { dao.save(Scrapbook(it.getString("id"), it.getString("title"), it.getString("theme"), it.getLong("updatedAt"))) }
                // Page IDs have no external references: assign fresh IDs to protect existing books.
                objects(m, "pages").filter { it.getString("bookId") !in existingBooks }.forEach { dao.save(BookPage(UUID.randomUUID().toString(), it.getString("bookId"), it.getString("memoryId"), it.getInt("position"), it.getString("caption"), it.getString("layout"))) }
                objects(m, "media").filter { it.getString("memoryId") !in existingMemories }.forEach { x ->
                    val name = UUID.randomUUID().toString() + if (x.getString("kind") == "audio") ".m4a" else ".photo"
                    val target = repo.file(name); createdFiles.add(target); target.writeBytes(archive.files.getValue("media/${x.getString("filename")}"))
                    dao.save(Attachment(UUID.randomUUID().toString(), x.getString("memoryId"), name, x.getString("kind"), x.getString("name"), x.getLong("durationMs")))
                }
            }
        } catch (e: Exception) { createdFiles.forEach { it.delete() }; throw e }
    }
    private fun readLimited(input: InputStream, limit: Int): ByteArray {
        val out = ByteArrayOutputStream(); val buffer = ByteArray(8192); var total = 0
        while (true) { val n = input.read(buffer); if (n < 0) break; total += n; require(total <= limit); out.write(buffer, 0, n) }
        return out.toByteArray()
    }

    // The JSON reader owns its wrapper. The archive reader owns the ZIP stream.
    private class ManifestEntry(private val input: InputStream, private val limit: Int) : InputStream() {
        var count = 0
            private set

        override fun read(): Int = input.read().also { if (it != -1) record(1) }

        override fun read(buffer: ByteArray, offset: Int, length: Int): Int =
            input.read(buffer, offset, minOf(length, limit - count + 1)).also { if (it > 0) record(it) }

        private fun record(bytes: Int) {
            count += bytes
            require(count <= limit) { "Backup manifest exceeds its byte budget" }
        }
    }
}
