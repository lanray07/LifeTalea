import {createVerifier, receiptRequest, VerificationError} from '../src/verifier.mjs';
import {Buffer} from 'node:buffer';

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
      if(!await consumeQuota()) return reply(429,{error:'retry_later'});
      return reply(200,await verifier.verify(input,request.signal));
    } catch(error) {
      return reply(error instanceof VerificationError?error.status:503,{error:error instanceof VerificationError?error.code:'verification_unavailable'});
    }
  };
}

export function productionVerifier(env) {
  return createVerifier({environment:'production',sharedSecret:env('LIFETALEA_AMAZON_SHARED_SECRET'),privateKey:Buffer.from(env('LIFETALEA_RVS_PRIVATE_KEY_PEM_B64')??'','base64').toString('utf8'),ttlMs:86400000,allowAmazonTestTransactions:env('LIFETALEA_ALLOW_AMAZON_TEST_TRANSACTIONS')==='true'});
}
