// Simple encryption utility for API token display
// Uses browser-compatible crypto functions for basic obfuscation

class TokenEncryption {
  constructor() {
    // Simple key for basic obfuscation (not for security, just display)
    this.key = 'apk_finder_token_key'
  }

  // Simple XOR encryption for display purposes
  encrypt(text) {
    if (!text) return ''
    
    try {
      let result = ''
      for (let i = 0; i < text.length; i++) {
        result += String.fromCharCode(
          text.charCodeAt(i) ^ this.key.charCodeAt(i % this.key.length)
        )
      }
      
      // Base64 encode the result for safe storage
      return btoa(result)
    } catch (error) {
      console.error('Encryption failed:', error)
      return text // Return original if encryption fails
    }
  }

  // Simple XOR decryption
  decrypt(encryptedText) {
    if (!encryptedText) return ''
    
    try {
      // Decode from base64
      const decoded = atob(encryptedText)
      
      let result = ''
      for (let i = 0; i < decoded.length; i++) {
        result += String.fromCharCode(
          decoded.charCodeAt(i) ^ this.key.charCodeAt(i % this.key.length)
        )
      }
      
      return result
    } catch (error) {
      console.error('Decryption failed:', error)
      return encryptedText // Return original if decryption fails
    }
  }

  // Generate masked display text (显示密文)
  getMaskedDisplay(text) {
    if (!text) return ''
    
    const length = text.length
    if (length <= 4) {
      return '*'.repeat(length)
    }
    
    // Show first 2 and last 2 characters, mask the rest
    return text.substring(0, 2) + '*'.repeat(length - 4) + text.substring(length - 2)
  }

  // Check if a string appears to be encrypted (base64)
  isEncrypted(text) {
    if (!text) return false
    
    try {
      // Check if it's valid base64
      return btoa(atob(text)) === text
    } catch (error) {
      return false
    }
  }
}

// Create and export singleton instance
export const tokenEncryption = new TokenEncryption()
export default tokenEncryption