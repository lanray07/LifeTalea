/** Loopback-only App Tester transport. Never a public/production deployment entrypoint. */
import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {createServer} from 'node:https';
import {createVerifier} from '../src/verifier.mjs';
import {createReceiptServer} from '../src/http.mjs';

const context=JSON.parse(readFileSync(process.argv[2],'utf8'));
if(context.environment!=='sandbox' || context.endpoint!=='https://localhost:8443/v1/verify' || process.env.NODE_TLS_REJECT_UNAUTHORIZED==='0')throw Error('Local sandbox configuration required');
const verifier=createVerifier({environment:'sandbox',sharedSecret:'local-app-tester-only',privateKey:readFileSync(join(context.privateDirectory,'assertion.private.pem')),ttlMs:6*60*60*1000});
const counters={verifiedActive:0,verifiedInactive:0,unavailable:0};
const http=createReceiptServer({environment:'sandbox',async verify(input,signal){
  try{
    const result=await verifier.verify(input,signal);
    const claims=JSON.parse(Buffer.from(result.assertion.split('.')[0],'base64url'));
    counters[claims.active?'verifiedActive':'verifiedInactive']++;
    return result;
  }catch(error){counters.unavailable++;throw error;}
}});
const tls=createServer({key:readFileSync(join(context.privateDirectory,'tls.private.pem')),cert:readFileSync(join(context.privateDirectory,'tls.crt'))},(req,res)=>{
  if(req.url==='/qa/status'&&req.method==='GET'){
    res.writeHead(200,{'content-type':'application/json','cache-control':'no-store'});res.end(JSON.stringify({environment:'sandbox',...counters}));return;
  }
  http.emit('request',req,res);
});
tls.headersTimeout=5000;tls.requestTimeout=10000;tls.keepAliveTimeout=2000;tls.maxHeadersCount=32;
tls.listen(8443,'127.0.0.1',()=>process.stdout.write('Local sandbox HTTPS verifier listening on loopback:8443; no customer identifiers are logged\n'));
for(const signal of ['SIGTERM','SIGINT'])process.once(signal,()=>{tls.close();tls.closeAllConnections();});
