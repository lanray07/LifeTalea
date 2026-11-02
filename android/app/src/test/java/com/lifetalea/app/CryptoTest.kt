package com.lifetalea.app
import com.lifetalea.app.data.ArchiveCrypto
import org.junit.Assert.*
import org.junit.Test
class CryptoTest {
    @Test fun authenticatedRoundTripAndTamperRejection() {
        val source = "A private family story".toByteArray(); val password = "long passphrase".toCharArray()
        val encrypted = ArchiveCrypto.encrypt(source, password)
        assertArrayEquals(source, ArchiveCrypto.decrypt(encrypted, password))
        assertFalse(source.contentEquals(encrypted)); encrypted[encrypted.lastIndex] = (encrypted.last().toInt() xor 1).toByte()
        assertThrows(Exception::class.java) { ArchiveCrypto.decrypt(encrypted, password) }
    }
    @Test fun wrongPasswordDoesNotReturnPlaintext() {
        val encrypted = ArchiveCrypto.encrypt(byteArrayOf(1, 2), "correct password".toCharArray())
        assertThrows(Exception::class.java) { ArchiveCrypto.decrypt(encrypted, "incorrect password".toCharArray()) }
    }
}
