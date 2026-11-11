import {createVerifier, receiptRequest, VerificationError} from '../src/verifier.mjs';
import {Buffer} from 'node:buffer';
import {createHmac} from 'node:crypto';
import {isIP} from 'node:net';

const headers = {'content-type':'application/json; charset=utf-8','cache-control':'no-store','x-content-type-options':'nosniff','content-security-policy':"default-src 'none'"};
const reply = (status, value) => new Response(JSON.stringify(value), {status,headers:{...headers,...(status===429?{'retry-after':'2'}:{})}});

/** Receipt possession is checked against Amazon before any signed entitlement is issued.
 * This app has no Supabase user accounts. Never trust an app-embedded shared secret.
 * The SQL quota is shared across isolates and contains no customer identifiers.
 */
export function edgeHandler({verifier, consumeQuota}) {
  return async request => {
    const path = new URL(request.url).pathname;
    if (path.endsWith('/health') && request.method==='GET') return reply(200,{service:'lifetalea-amazon-rvs',version:1,environment:'production',ready:!!verifier});
    if (!path.endsWith('/v1/verify')) return reply(404,{error:'not_found'});
    if (request.method!=='POST') return reply(405,{error:'method_not_allowed'});
    if (!/^application\/json(?:\s*;\s*charset=utf-8)?$/i.test(request.headers.get('content-type')??'')) return reply(415,{error:'json_required'});
    if (!verifier) return reply(503,{error:'verification_unavailable'});
    const length=request.headers.get('content-length');
    if (length && (!/^\d+$/.test(length)||Number(length)>2048)) return reply(413,{error:'request_too_large'});
    const reader=request.body?.getReader();
    if (!reader) return reply(400,{error:'invalid_request'});
    try {
      const deadline=AbortSignal.timeout(5000); let size=0; const chunks=[];
      const abort=()=>{void reader.cancel().catch(()=>{});};
      deadline.addEventListener('abort',abort,{once:true});
      try {
        while(true) {
          const {done,value}=await reader.read(); if(done) break;
          size+=value.byteLength; if(size>2048) return reply(413,{error:'request_too_large'});
          chunks.push(value);
        }
        if(deadline.aborted) return reply(408,{error:'request_timeout'});
      } finally {deadline.removeEventListener('abort',abort); await reader.cancel().catch(()=>{});reader.releaseLock();}
      let input;
      try {input=receiptRequest(JSON.parse(Buffer.concat(chunks).toString('utf8')));} catch {return reply(400,{error:'invalid_request'});}
      if(!await consumeQuota(request)) return reply(429,{error:'retry_later'});
      return reply(200,await verifier.verify(input,request.signal));
    } catch(error) {
      return reply(error instanceof VerificationError?error.status:503,{error:error instanceof VerificationError?error.code:'verification_unavailable'});
    }
  };
}

// On the hosted Supabase domain this header is set by Cloudflare at ingress.
// Never fall back to a caller-supplied forwarding chain or receipt identifier.
export function sourceQuotaSlot(address, secret) {
  const family = isIP(address ?? '');
  if (!family || !secret) throw new VerificationError(503, 'verification_unavailable');
  let source = address;
  if (family === 6) {
    const canonical = new URL('http://[' + address + ']').hostname.slice(1, -1);
    const [left, right] = canonical.split('::');
    const first = left ? left.split(':') : [];
    const last = right ? right.split(':') : [];
    const words = right === undefined ? first : [...first, ...Array(8 - first.length - last.length).fill('0'), ...last];
    source = words.slice(0, 4).join(':');
    // Fold IPv4-mapped addresses into the same source as their IPv4 spelling.
    if (words.slice(0, 5).every(word => word === '0') && words[5] === 'ffff') {
      source = words.slice(6).flatMap(word => [parseInt(word, 16) >> 8, parseInt(word, 16) & 255]).join('.');
    }
  }
  const digest = createHmac('sha256', secret).update('lifetalea:rvs-source:v1:').update(source).digest();
  return digest.readUInt16BE(0) % 4096;
}

export function productionVerifier(env) {
  return createVerifier({environment:'production',sharedSecret:env('LIFETALEA_AMAZON_SHARED_SECRET'),privateKey:Buffer.from(env('LIFETALEA_RVS_PRIVATE_KEY_PEM_B64')??'','base64').toString('utf8'),ttlMs:86400000,allowAmazonTestTransactions:env('LIFETALEA_ALLOW_AMAZON_TEST_TRANSACTIONS')==='true'});
}
