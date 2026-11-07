package com.lifetalea.app.data

import android.content.Context
import android.net.Uri
import androidx.room.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import java.io.File
import java.time.LocalDate
import java.util.UUID

@Entity(tableName = "memories")
data class Memory(
    @PrimaryKey val id: String = UUID.randomUUID().toString(),
    val title: String = "", val story: String = "", val date: String = "",
    val precision: String = "UNKNOWN", val location: String = "", val tags: String = "",
    val transcript: String = "", val favourite: Boolean = false,
    val createdAt: Long = System.currentTimeMillis(), val updatedAt: Long = System.currentTimeMillis()
)
@Entity(tableName = "albums")
data class Album(@PrimaryKey val id: String = UUID.randomUUID().toString(), val title: String, val theme: String = "forest")
@Entity(tableName = "album_memories", primaryKeys = ["albumId", "memoryId"], foreignKeys = [
    ForeignKey(entity = Album::class, parentColumns = ["id"], childColumns = ["albumId"], onDelete = ForeignKey.CASCADE),
    ForeignKey(entity = Memory::class, parentColumns = ["id"], childColumns = ["memoryId"], onDelete = ForeignKey.CASCADE)
], indices = [Index("memoryId")])
data class AlbumMemory(val albumId: String, val memoryId: String)
@Entity(tableName = "media", foreignKeys = [ForeignKey(entity = Memory::class, parentColumns = ["id"], childColumns = ["memoryId"], onDelete = ForeignKey.CASCADE)], indices = [Index("memoryId")])
data class Attachment(@PrimaryKey val id: String = UUID.randomUUID().toString(), val memoryId: String, val filename: String, val kind: String, val name: String, val durationMs: Long = 0)
@Entity(tableName = "scrapbooks")
data class Scrapbook(@PrimaryKey val id: String = UUID.randomUUID().toString(), val title: String, val theme: String = "forest", val updatedAt: Long = System.currentTimeMillis())
@Entity(tableName = "pages", foreignKeys = [ForeignKey(entity = Scrapbook::class, parentColumns = ["id"], childColumns = ["bookId"], onDelete = ForeignKey.CASCADE)], indices = [Index("bookId")])
data class BookPage(@PrimaryKey val id: String = UUID.randomUUID().toString(), val bookId: String, val memoryId: String, val position: Int, val caption: String = "", val layout: String = "story")

@Dao
interface LibraryDao {
    @Query("SELECT * FROM memories ORDER BY updatedAt DESC") fun memories(): Flow<List<Memory>>
    @Query("SELECT * FROM albums ORDER BY title COLLATE NOCASE") fun albums(): Flow<List<Album>>
    @Query("SELECT * FROM album_memories") fun links(): Flow<List<AlbumMemory>>
    @Query("SELECT * FROM media") fun media(): Flow<List<Attachment>>
    @Query("SELECT * FROM scrapbooks ORDER BY updatedAt DESC") fun books(): Flow<List<Scrapbook>>
    @Query("SELECT * FROM pages ORDER BY position") fun pages(): Flow<List<BookPage>>
    @Query("SELECT * FROM memories") suspend fun allMemories(): List<Memory>
    @Query("SELECT * FROM albums") suspend fun allAlbums(): List<Album>
    @Query("SELECT * FROM album_memories") suspend fun allLinks(): List<AlbumMemory>
    @Query("SELECT * FROM media") suspend fun allMedia(): List<Attachment>
    @Query("SELECT * FROM scrapbooks") suspend fun allBooks(): List<Scrapbook>
    @Query("SELECT * FROM pages ORDER BY position") suspend fun allPages(): List<BookPage>
    @Upsert suspend fun save(memory: Memory)
    @Upsert suspend fun save(album: Album)
    @Upsert suspend fun save(book: Scrapbook)
    @Upsert suspend fun save(page: BookPage)
    @Upsert suspend fun save(attachment: Attachment)
    @Query("UPDATE memories SET transcript = CASE WHEN transcript = '' THEN :draft ELSE transcript || char(10) || char(10) || :draft END, updatedAt = :now WHERE id = :id AND length(transcript) + length(:draft) + CASE WHEN transcript = '' THEN 0 ELSE 2 END <= 1000000")
    suspend fun appendTranscript(id: String, draft: String, now: Long): Int
    @Insert(onConflict = OnConflictStrategy.IGNORE) suspend fun link(link: AlbumMemory)
    @Query("DELETE FROM album_memories WHERE memoryId = :id") suspend fun unlink(id: String)
    @Query("DELETE FROM memories WHERE id = :id") suspend fun deleteMemory(id: String)
    @Query("DELETE FROM albums WHERE id = :id") suspend fun deleteAlbum(id: String)
    @Query("DELETE FROM media WHERE id = :id") suspend fun deleteMedia(id: String)
    @Query("DELETE FROM pages WHERE id = :id") suspend fun deletePage(id: String)
    @Query("DELETE FROM scrapbooks WHERE id = :id") suspend fun deleteBook(id: String)
    @Query("DELETE FROM memories") suspend fun clearMemories()
    @Query("DELETE FROM albums") suspend fun clearAlbums()
    @Query("DELETE FROM scrapbooks") suspend fun clearBooks()
}

@Database(entities = [Memory::class, Album::class, AlbumMemory::class, Attachment::class, Scrapbook::class, BookPage::class], version = 1, exportSchema = true)
abstract class LifeDatabase : RoomDatabase() {
    abstract fun library(): LibraryDao
    companion object {
        @Volatile private var instance: LifeDatabase? = null
        fun open(context: Context): LifeDatabase = instance ?: synchronized(this) {
            instance ?: Room.databaseBuilder(context.applicationContext, LifeDatabase::class.java, "lifetalea.db")
                .build().also { instance = it }
        }
    }
}

object MemoryRules {
    fun formattedDate(memory: Memory, locale: java.util.Locale): String = runCatching {
        val decimal = java.time.format.DecimalStyle.of(locale)
        when (memory.precision) {
            "YEAR" -> java.text.NumberFormat.getIntegerInstance(locale).apply { isGroupingUsed = false }.format(memory.date.toInt())
            "MONTH" -> java.time.YearMonth.parse(memory.date).format(java.time.format.DateTimeFormatter.ofPattern("LLLL yyyy",locale).withDecimalStyle(decimal))
            "DAY" -> LocalDate.parse(memory.date).format(java.time.format.DateTimeFormatter.ofLocalizedDate(java.time.format.FormatStyle.MEDIUM).withLocale(locale).withDecimalStyle(decimal))
            else -> ""
        }
    }.getOrDefault(memory.date)
    /** Dates remain ISO in storage, while accepting decimal digits from local keyboards. */
    fun normaliseDateDigits(input: String): String = input.map { character ->
        val digit = Character.digit(character, 10)
        if (digit >= 0) ('0'.code + digit).toChar() else character
    }.joinToString("")
    fun validDate(date: String, precision: String): Boolean = runCatching {
        when (precision) {
            "UNKNOWN" -> require(date.isEmpty())
            "YEAR" -> require(date.matches(Regex("[0-9]{4}")) && date.toInt() in 1..9999)
            "MONTH" -> { require(date.matches(Regex("[0-9]{4}-[0-9]{2}"))); require(java.time.YearMonth.parse(date).year in 1..9999) }
            "DAY" -> { require(date.matches(Regex("[0-9]{4}-[0-9]{2}-[0-9]{2}"))); require(LocalDate.parse(date).year in 1..9999) }
            else -> error("Invalid precision")
        }; true
    }.getOrDefault(false)
    fun matches(m: Memory, query: String) = query.trim().lowercase().let { q ->
        listOf(m.title, m.story, m.tags, m.transcript, m.location, m.date).any { it.lowercase().contains(q) }
    }
    fun timeline(memories: List<Memory>) = memories.sortedWith(compareByDescending<Memory> { it.date.ifEmpty { "0000" } }.thenByDescending { it.createdAt })
}

class LibraryRepository(val context: Context, val db: LifeDatabase) {
    val dao = db.library()
    val mediaDir = File(context.filesDir, "media").apply { mkdirs() }
    fun file(name: String): File { require(name.matches(Regex("[a-zA-Z0-9._-]{1,100}")) && name != "." && name != ".."); return File(mediaDir, name) }
    suspend fun save(memory: Memory, albumIds: Set<String>) = withContext(Dispatchers.IO) {
        require(memory.title.isNotBlank() && memory.title.length <= 300)
        require(MemoryRules.validDate(memory.date, memory.precision))
        db.withTransaction { dao.save(memory.copy(updatedAt = System.currentTimeMillis())); dao.unlink(memory.id); albumIds.forEach { dao.link(AlbumMemory(it, memory.id)) } }
    }
    suspend fun importPhoto(id: String, uri: Uri) = withContext(Dispatchers.IO) {
        val filename = UUID.randomUUID().toString() + ".photo"
        val target = file(filename)
        try {
            context.contentResolver.openInputStream(uri)!!.use { input -> target.outputStream().use { output ->
                val buffer = ByteArray(8192); var total = 0L
                while (true) { val n = input.read(buffer); if (n < 0) break; total += n; require(total <= 40L * 1024 * 1024); output.write(buffer, 0, n) }
            } }
            val options = android.graphics.BitmapFactory.Options().apply { inJustDecodeBounds = true }
            android.graphics.BitmapFactory.decodeFile(target.path, options)
            require(options.outWidth > 0 && options.outHeight > 0)
            dao.save(Attachment(memoryId = id, filename = filename, kind = "photo", name = "Photo"))
        } catch (e: Exception) { target.delete(); throw e }
    }
    /** Each duplicate owns its files so deleting either memory cannot damage the other. */
    suspend fun duplicate(id: String): Memory = withContext(Dispatchers.IO) {
        val createdFiles = mutableListOf<File>()
        try {
            db.withTransaction {
                val original = dao.allMemories().first { it.id == id }
                val now = System.currentTimeMillis()
                val duplicate = original.copy(id = UUID.randomUUID().toString(), createdAt = now, updatedAt = now)
                dao.save(duplicate)
                dao.allLinks().filter { it.memoryId == id }.forEach { dao.link(it.copy(memoryId = duplicate.id)) }
                dao.allMedia().filter { it.memoryId == id }.forEach { attachment ->
                    val name = UUID.randomUUID().toString() + if (attachment.kind == "audio") ".m4a" else ".photo"
                    val target = file(name)
                    createdFiles.add(target)
                    file(attachment.filename).copyTo(target)
                    dao.save(attachment.copy(id = UUID.randomUUID().toString(), memoryId = duplicate.id, filename = name))
                }
                duplicate
            }
        } catch (e: Exception) { createdFiles.forEach { it.delete() }; throw e }
    }
    suspend fun removeMemory(id: String) = withContext(Dispatchers.IO) {
        val files = dao.allMedia().filter { it.memoryId == id }.map { file(it.filename) }
        dao.deleteMemory(id); files.forEach { it.delete() }
    }
    suspend fun removeMedia(a: Attachment) = withContext(Dispatchers.IO) { dao.deleteMedia(a.id); file(a.filename).delete(); Unit }
    suspend fun clearAll() = withContext(Dispatchers.IO) {
        db.withTransaction { dao.clearBooks(); dao.clearMemories(); dao.clearAlbums() }
        mediaDir.listFiles()?.forEach { it.delete() }
    }
}
