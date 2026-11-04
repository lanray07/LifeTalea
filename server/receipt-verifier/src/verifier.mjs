import {createPrivateKey, createPublicKey, sign} from 'node:crypto';
import {Buffer} from 'node:buffer';

export const SKU = 'com.lifetalea.premium';
export const AUDIENCE = 'com.lifetalea.app';
export const MAX_TTL = 24 * 60 * 60 * 1000;
export class VerificationError extends Error {
  constructor(status, code) { super(code); this.status = status; this.code = code; }
}
const invalid = () => new VerificationError(400, 'invalid_request');
export function receiptRequest(value) {
  if (!value || Array.isArray(value) || typeof value !== 'object' || Object.keys(value).sort().join(',') !== 'receiptId,userId') throw invalid();
  for (const [field, limit] of [['userId',256], ['receiptId',512]]) {
    const text = value[field];
    if (typeof text !== 'string' || !text.length || text.length > limit || !/^[\x21-\x7e]+$/.test(text) || ['.','..'].includes(text)) throw invalid();
  }
  return {userId: value.userId, receiptId: value.receiptId};
}
export function signingKey(pem) {
  try {
    const key = createPrivateKey(pem);
    if (key.asymmetricKeyType !== 'rsa' || key.asymmetricKeyDetails.modulusLength < 2048) throw Error();
    return key;
  } catch { throw new Error('RVS signing key must be an RSA private key of at least 2048 bits'); }
}
export function publicKeyBase64(privateKey) {
  return createPublicKey(privateKey).export({type:'spki',format:'der'}).toString('base64');
}
async function boundedJson(response, limit = 64 * 1024) {
  if (!response.body) throw new VerificationError(503, 'verification_unavailable');
  const reader = response.body.getReader(); let total = 0; const chunks = [];
  try {
    while (true) {
      const {done,value} = await reader.read(); if (done) break;
      total += value.length;
      if (total > limit) throw Error();
      chunks.push(value);
    }
    return JSON.parse(Buffer.concat(chunks).toString('utf8'));
  } catch { await reader.cancel().catch(()=>{}); throw new VerificationError(503,'verification_unavailable'); }
  finally { reader.releaseLock(); }
}
/** Transport injection is for offline contract tests. The executable always uses native fetch. */
export function createVerifier(config, transport = fetch, now = Date.now) {
  if (!['production','sandbox'].includes(config.environment) || typeof config.sharedSecret !== 'string' || config.sharedSecret.length < 1) throw Error('Invalid RVS environment/secret configuration');
  if (!Number.isSafeInteger(config.ttlMs) || config.ttlMs <= 0 || config.ttlMs > MAX_TTL) throw Error('Invalid assertion lifetime');
  const key = signingKey(config.privateKey);
  function assertion(request, active, reason, testTransaction = false, betaProduct = false) {
    const issuedAt = now();
    const payload = {v:1, iss:'lifetalea-amazon-rvs', aud:AUDIENCE, sub:request.userId, receiptId:request.receiptId, sku:SKU, environment:config.environment, active, reason, testTransaction, betaProduct, iat:issuedAt, exp:issuedAt+config.ttlMs};
    const data = Buffer.from(JSON.stringify(payload)).toString('base64url');
    return {assertion: data+'.'+sign('RSA-SHA256', Buffer.from(data,'ascii'), key).toString('base64url')};
  }
  return {
    environment: config.environment,
    publicKey: publicKeyBase64(key),
    async verify(input, signal) {
      const request = receiptRequest(input);
      // No caller-controlled host, environment, SKU, shared secret or redirect target.
      const prefix = config.environment === 'sandbox' ? '/sandbox' : '';
      const url = 'https://appstore-sdk.amazon.com'+prefix+'/version/1.0/verifyReceiptId/developer/'+encodeURIComponent(config.sharedSecret)+'/user/'+encodeURIComponent(request.userId)+'/receiptId/'+encodeURIComponent(request.receiptId);
      try {
        const timeout = AbortSignal.timeout(config.timeoutMs ?? 8000);
        const response = await transport(url, {method:'GET',redirect:'manual',signal:signal ? AbortSignal.any([signal,timeout]) : timeout,headers:{accept:'application/json'}});
        if (response.status !== 200) {
          await response.body?.cancel().catch(()=>{});
          if ([400,410,497].includes(response.status)) return assertion(request,false,response.status===410?'canceled':'invalid_receipt');
          throw new VerificationError(503,'verification_unavailable');
        }
        const receipt = await boundedJson(response);
        if (!receipt || receipt.receiptId !== request.receiptId || receipt.productId !== SKU || receipt.productType !== 'ENTITLED' ||
            typeof receipt.betaProduct !== 'boolean' || typeof receipt.testTransaction !== 'boolean' ||
            !Object.hasOwn(receipt,'cancelDate') || !(receipt.cancelDate === null || (Number.isSafeInteger(receipt.cancelDate) && receipt.cancelDate >= 0)) ||
            !Number.isSafeInteger(receipt.purchaseDate) || receipt.purchaseDate < 0 || receipt.purchaseDate > now()+300000) {
          throw new VerificationError(503,'verification_unavailable');
        }
        // Amazon's production publishing/LAT transactions are distinct from App Tester sandbox receipts.
        if (config.environment === 'production' && (receipt.testTransaction || receipt.betaProduct) && !config.allowAmazonTestTransactions) {
          return assertion(request,false,'test_transaction_disabled',receipt.testTransaction,receipt.betaProduct);
        }
        return assertion(request,receipt.cancelDate===null,receipt.cancelDate===null?'active':'canceled',receipt.testTransaction,receipt.betaProduct);
      } catch (error) {
        if (error instanceof VerificationError) throw error;
        // Never return the upstream URL/error: it contains the developer secret and account/receipt IDs.
        throw new VerificationError(503,'verification_unavailable');
      }
    }
  };
}
