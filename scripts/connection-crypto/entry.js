import { gcm } from '@noble/ciphers/aes.js';
import { pbkdf2Async } from '@noble/hashes/pbkdf2.js';
import { sha256 } from '@noble/hashes/sha2.js';
export async function crypt(password, salt, iv, aad, input, decrypt = false) {
  const key = await pbkdf2Async(sha256, new TextEncoder().encode(password), salt, { c: 600000, dkLen: 32, asyncTick: 10 });
  try { return gcm(key, iv, aad)[decrypt ? 'decrypt' : 'encrypt'](input); }
  finally { key.fill(0); }
}
