package com.lifetalea.app.data

import android.util.JsonReader
import android.util.JsonToken
import java.io.InputStream
import java.io.InputStreamReader
import org.json.JSONArray
import org.json.JSONObject

internal object BackupManifest {
    const val MAX_RECORDS = 10_000

    private enum class Field { TEXT, INTEGER, BOOLEAN }

    private fun fields(text: List<String>, integer: List<String> = emptyList(), boolean: List<String> = emptyList()) =
        text.associateWith { Field.TEXT } + integer.associateWith { Field.INTEGER } + boolean.associateWith { Field.BOOLEAN }

    private val collections = mapOf(
        "memories" to fields(
            listOf("id", "title", "story", "date", "precision", "location", "tags", "transcript"),
            listOf("createdAt", "updatedAt"),
            listOf("favourite")
        ),
        "albums" to fields(listOf("id", "title", "theme")),
        "links" to fields(listOf("albumId", "memoryId")),
        "books" to fields(listOf("id", "title", "theme"), listOf("updatedAt")),
        "pages" to fields(listOf("id", "bookId", "memoryId", "caption", "layout"), listOf("position")),
        "media" to fields(listOf("id", "memoryId", "filename", "kind", "name", "sha256"), listOf("durationMs"))
    )

    fun read(input: InputStream): JSONObject =
        JsonReader(InputStreamReader(input, Charsets.UTF_8.newDecoder())).use { reader ->
            val manifest = JSONObject()
            reader.beginObject()
            while (reader.hasNext()) {
                val name = reader.nextName()
                require(!manifest.has(name)) { "Duplicate backup field" }
                when (name) {
                    "format" -> {
                        require(reader.peek() == JsonToken.STRING && reader.nextString() == "lifetalea")
                        manifest.put(name, "lifetalea")
                    }
                    "version" -> {
                        require(reader.peek() == JsonToken.NUMBER && reader.nextString().toLongOrNull() == 1L)
                        manifest.put(name, 1)
                    }
                    else -> manifest.put(name, readCollection(reader, requireNotNull(collections[name])))
                }
            }
            reader.endObject()
            require(reader.peek() == JsonToken.END_DOCUMENT)
            require(manifest.length() == collections.size + 2)
            manifest
        }

    private fun readCollection(reader: JsonReader, schema: Map<String, Field>): JSONArray {
        val result = JSONArray()
        reader.beginArray()
        while (reader.hasNext()) {
            require(result.length() < MAX_RECORDS) { "Too many backup records" }
            val record = JSONObject()
            reader.beginObject()
            while (reader.hasNext()) {
                val name = reader.nextName()
                require(!record.has(name)) { "Duplicate backup record field" }
                when (requireNotNull(schema[name])) {
                    Field.TEXT -> {
                        require(reader.peek() == JsonToken.STRING)
                        val value = reader.nextString()
                        if (name == "story" || name == "transcript") require(value.length <= 1_000_000)
                        record.put(name, value)
                    }
                    Field.INTEGER -> {
                        require(reader.peek() == JsonToken.NUMBER)
                        val value = requireNotNull(reader.nextString().toLongOrNull())
                        if (name == "position") require(value in 0..Int.MAX_VALUE.toLong())
                        record.put(name, value)
                    }
                    Field.BOOLEAN -> {
                        require(reader.peek() == JsonToken.BOOLEAN)
                        record.put(name, reader.nextBoolean())
                    }
                }
            }
            reader.endObject()
            require(record.length() == schema.size) { "Incomplete backup record" }
            result.put(record)
        }
        reader.endArray()
        return result
    }
}
