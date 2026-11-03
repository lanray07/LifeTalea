import test from 'node:test';
import assert from 'node:assert/strict';
import {generateKeyPairSync,verify,createPrivateKey,createPublicKey} from 'node:crypto';
import {once} from 'node:events';
import {readFileSync,mkdtempSync,unlinkSync,rmdirSync,existsSync} from 'node:fs';
import {spawn,spawnSync} from 'node:child_process';
import {createServer as httpServer} from 'node:http';
import {fileURLToPath} from 'node:url';
import {tmpdir} from 'node:os';
import {join,resolve,dirname} from 'node:path';
import {createVerifier,receiptRequest,SKU,MAX_TTL} from '../src/verifier.mjs';
import {createReceiptServer,createLimiter} from '../src/http.mjs';

const keys=generateKeyPairSync('rsa',{modulusLength:2048});
const pem=keys.privateKey.export({type:'pkcs8',format:'pem'});
const now=1700000000000;
const input={userId:'fictional-user/+:=',receiptId:'fictional-receipt/+:='};
const config={environment:'production',sharedSecret:'fictional-server-secret',privateKey:pem,ttlMs:3600000};
const receipt=(overrides={})=>({receiptId:input.receiptId,productId:SKU,productType:'ENTITLED',cancelDate:null,purchaseDate:now-1000,betaProduct:false,testTransaction:false,...overrides});
const response=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'content-type':'application/json'}});
function decode(result) {
  const [payload,signature]=result.assertion.split('.');
  assert.ok(verify('RSA-SHA256',Buffer.from(payload,'ascii'),keys.publicKey,Buffer.from(signature,'base64url')));
  return JSON.parse(Buffer.from(payload,'base64url'));
}
test('real RSA signature binds active entitlement, identity, receipt, SKU, environment and expiry',async()=>{
  let seen;
  const verifier=createVerifier(config,async(url,options)=>{seen={url,options};return response(receipt());},()=>now);
  const c=decode(await verifier.verify(input));
  assert.deepEqual([c.sub,c.receiptId,c.sku,c.environment,c.active,c.iat,c.exp],[input.userId,input.receiptId,SKU,'production',true,now,now+3600000]);
  assert.ok(seen.url.startsWith('https://appstore-sdk.amazon.com/version/1.0/'));
  assert.ok(seen.url.endsWith('/user/fictional-user%2F%2B%3A%3D/receiptId/fictional-receipt%2F%2B%3A%3D'));
  assert.equal(seen.options.redirect,'manual'); assert.ok(seen.options.signal);
});
test('sandbox has a fixed distinct upstream and signed environment',async()=>{
  let url;
  const v=createVerifier({...config,environment:'sandbox'},async u=>{url=u;return response(receipt({testTransaction:true}));},()=>now);
  const c=decode(await v.verify(input));assert.equal(c.environment,'sandbox');assert.ok(c.active);assert.ok(url.startsWith('https://appstore-sdk.amazon.com/sandbox/version/1.0/'));
});
test('cancelDate, including zero, revokes entitlement',async()=>{
  for(const cancelDate of [0,now]) assert.equal(decode(await createVerifier(config,async()=>response(receipt({cancelDate})),()=>now).verify(input)).active,false);
});
test('Amazon invalid, canceled and mismatched-user statuses produce signed inactive decisions',async()=>{
  for(const status of [400,410,497]) assert.equal(decode(await createVerifier(config,async()=>response({},status),()=>now).verify(input)).active,false);
});
test('throttling, secret failure, server errors and redirects fail closed without leaking upstream errors',async()=>{
  for(const status of [429,496,500,302]) await assert.rejects(createVerifier(config,async()=>response({secret:config.sharedSecret},status),()=>now).verify(input),e=>e.status===503&&!e.message.includes(config.sharedSecret));
});
test('wrong receipt, SKU/type, malformed cancellation, missing flags and future purchase cannot grant',async()=>{
  for(const overrides of [{receiptId:'other'},{productId:'other'},{productType:'CONSUMABLE'},{cancelDate:'0'},{cancelDate:undefined},{betaProduct:undefined},{testTransaction:'false'},{purchaseDate:now+300001}]) {
    await assert.rejects(createVerifier(config,async()=>response(receipt(overrides)),()=>now).verify(input));
  }
});
test('production publishing/LAT test receipts require explicit server opt-in; sandbox is still distinct',async()=>{
  const fake=async()=>response(receipt({testTransaction:true,betaProduct:true}));
  assert.equal(decode(await createVerifier(config,fake,()=>now).verify(input)).active,false);
  const c=decode(await createVerifier({...config,allowAmazonTestTransactions:true},fake,()=>now).verify(input));
  assert.ok(c.active);assert.equal(c.environment,'production');assert.ok(c.betaProduct);
});
test('oversized, absent and malformed Amazon JSON is rejected',async()=>{
  for(const fake of [()=>new Response('x'.repeat(65537)),()=>new Response(null),()=>new Response('{')]) await assert.rejects(createVerifier(config,async()=>fake(),()=>now).verify(input));
});
test('transport exceptions are redacted; cancellation signal is propagated',async()=>{
  const controller=new AbortController();controller.abort();
  await assert.rejects(createVerifier(config,async(_url,{signal})=>{assert.ok(signal.aborted);throw Error(config.sharedSecret);},()=>now).verify(input,controller.signal),e=>e.message==='verification_unavailable');
});
test('request cannot select environment, SKU, upstream host or secret; path-dot and whitespace rejected',()=>{
  for(const data of [null,[],{}, {...input,environment:'sandbox'},{...input,host:'localhost'},{...input,receiptId:'..'},{...input,userId:'\r\n'},{...input,receiptId:'a'.repeat(513)}]) assert.throws(()=>receiptRequest(data));
});
test('assertion lifetime and missing configuration are bounded',()=>{
  for(const cfg of [{...config,ttlMs:MAX_TTL+1},{...config,ttlMs:0},{...config,sharedSecret:''},{...config,environment:'other'},{...config,privateKey:'not a key'}]) assert.throws(()=>createVerifier(cfg));
});
test('global and per-client quotas are bounded and refill; forwarded headers are not trusted',()=>{
  let time=0;const allow=createLimiter(()=>time);
  for(let i=0;i<5;i++) assert.ok(allow('one'));
  assert.equal(allow('two'),false);time+=1000;assert.ok(allow('two'));assert.ok(allow('one'));assert.equal(allow('one'),false);
});
test('HTTP boundary verifies real JSON requests and returns a signed token with no-store headers',async t=>{
  const server=createReceiptServer(createVerifier(config,async()=>response(receipt()),()=>now),{limiter:()=>true});
  server.listen(0,'127.0.0.1');await once(server,'listening');t.after(()=>{server.closeAllConnections();server.close();});
  const base=`http://127.0.0.1:${server.address().port}`;
  const health=await fetch(base+'/health');assert.equal((await health.json()).environment,'production');
  const result=await fetch(base+'/v1/verify',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(input)});
  assert.equal(result.status,200);assert.equal(result.headers.get('cache-control'),'no-store');assert.ok(decode(await result.json()).active);
  for(const [path,options,status] of [ ['/v1/verify',{},405],['/not-found',{},404],['/v1/verify',{method:'POST',body:'{}'},415],['/v1/verify',{method:'POST',headers:{'content-type':'application/json'},body:'{'},400],['/v1/verify',{method:'POST',headers:{'content-type':'application/json'},body:'x'.repeat(2049)},413]]) {
    assert.equal((await fetch(base+path,options)).status,status);
  }
});
test('HTTP quota prevents upstream verification',async t=>{
  let calls=0;const server=createReceiptServer({environment:'production',verify:async()=>{calls++;}},{limiter:()=>false});
  server.listen(0,'127.0.0.1');await once(server,'listening');t.after(()=>{server.closeAllConnections();server.close();});
  const r=await fetch(`http://127.0.0.1:${server.address().port}/v1/verify`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(input)});
  assert.equal(r.status,429);assert.equal(calls,0);assert.equal(r.headers.get('retry-after'),'2');
});
test('committed Android contract fixtures have valid Node signatures and no private key',()=>{
  const f=JSON.parse(readFileSync(new URL('../../../android/app/src/androidTest/assets/rvs-contract.json',import.meta.url)));
  assert.equal(f.provenance,'OFFLINE_CONTRACT_FIXTURE_NOT_AN_AMAZON_TRANSACTION');
  for(const [name,environment,active] of [['active','production',true],['canceled','production',false],['sandbox','sandbox',true]]) {
    const [payload,signature]=f[name].split('.');
    const publicKey={key:Buffer.from(f.publicKey,'base64'),type:'spki',format:'der'};
    assert.ok(verify('RSA-SHA256',Buffer.from(payload,'ascii'),publicKey,Buffer.from(signature,'base64url')));
    const c=JSON.parse(Buffer.from(payload,'base64url'));assert.equal(c.environment,environment);assert.equal(c.active,active);assert.equal(c.sub,f.userId);
  }
  assert.ok(!JSON.stringify(f).includes('PRIVATE KEY'));
});
test('upstream timeout aborts an actual pending verification',async()=>{
  const hold=setTimeout(()=>{},1000);
  try {
    await assert.rejects(createVerifier({...config,timeoutMs:20},async(_url,{signal})=>new Promise((resolve,reject)=>signal.addEventListener('abort',()=>reject(Error('aborted')),{once:true})),()=>now).verify(input),e=>e.code==='verification_unavailable');
  } finally { clearTimeout(hold); }
});
test('HTTP concurrency cap rejects extra work while an upstream request is pending',async t=>{
  let started,finish;const begun=new Promise(resolve=>{started=resolve;});const wait=new Promise(resolve=>{finish=resolve;});
  const server=createReceiptServer({environment:'production',verify:async()=>{started();await wait;return {assertion:'fixture'};}},{limiter:()=>true,maxConcurrent:1});
  server.listen(0,'127.0.0.1');await once(server,'listening');t.after(()=>{finish();server.closeAllConnections();server.close();});
  const url=`http://127.0.0.1:${server.address().port}/v1/verify`,options={method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(input)};
  const first=fetch(url,options);await begun;assert.equal((await fetch(url,options)).status,429);finish();assert.equal((await first).status,200);
});
test('executable rejects missing or invalid secret/key/bind configuration without printing secrets',()=>{
  const base={RVS_ENVIRONMENT:'production',AMAZON_SHARED_SECRET:config.sharedSecret,RVS_SIGNING_PRIVATE_KEY_PEM_B64:Buffer.from(pem).toString('base64'),HOST:'127.0.0.1',PORT:'8080'};
  for(const env of [{},{...base,AMAZON_SHARED_SECRET:'short'},{...base,RVS_SIGNING_PRIVATE_KEY_PEM_B64:'invalid'},{...base,RVS_SIGNING_PRIVATE_KEY_FILE:'also-set'},{...base,HOST:'public.example'},{...base,NODE_TLS_REJECT_UNAUTHORIZED:'0'}]) {
    const p=spawnSync(process.execPath,[fileURLToPath(new URL('../src/main.mjs',import.meta.url))],{env,encoding:'utf8',timeout:5000});
    assert.equal(p.status,1);assert.ok(p.stderr.includes('configuration failed'));assert.ok(!p.stderr.includes(config.sharedSecret));assert.ok(!p.stderr.includes(pem));
  }
});
test('configured executable starts a real local readiness endpoint', {timeout:10000},async t=>{
  const probe=httpServer();probe.listen(0,'127.0.0.1');await once(probe,'listening');const port=probe.address().port;await new Promise(resolve=>probe.close(resolve));
  const child=spawn(process.execPath,[fileURLToPath(new URL('../src/main.mjs',import.meta.url))],{env:{RVS_ENVIRONMENT:'production',AMAZON_SHARED_SECRET:config.sharedSecret,RVS_SIGNING_PRIVATE_KEY_PEM_B64:Buffer.from(pem).toString('base64'),HOST:'127.0.0.1',PORT:String(port)},stdio:['ignore','pipe','pipe']});
  t.after(()=>child.kill());await once(child.stdout,'data');
  const health=await fetch(`http://127.0.0.1:${port}/health`);assert.deepEqual(await health.json(),{service:'lifetalea-amazon-rvs',version:1,ready:true,environment:'production'});
});
test('signing-key helper writes a matching public pair and refuses to replace an existing identity',()=>{
  const directory=mkdtempSync(join(tmpdir(),'lifetalea-key-test-'));
  const privateFile=join(directory,'fixture.private.pem'),publicFile=join(directory,'fixture.public.b64');
  try {
    const helper=fileURLToPath(new URL('../scripts/generate-signing-key.mjs',import.meta.url));
    const first=spawnSync(process.execPath,[helper,privateFile,publicFile],{encoding:'utf8',timeout:20000});assert.equal(first.status,0);
    const original=readFileSync(privateFile);const derived=createPublicKey(createPrivateKey(original)).export({type:'spki',format:'der'});
    assert.deepEqual(derived,Buffer.from(readFileSync(publicFile,'utf8').trim(),'base64'));assert.ok(!first.stdout.includes('PRIVATE KEY'));
    const second=spawnSync(process.execPath,[helper,privateFile,publicFile],{encoding:'utf8',timeout:20000});assert.notEqual(second.status,0);assert.deepEqual(readFileSync(privateFile),original);
  } finally {
    for(const path of [privateFile,publicFile]) {assert.equal(dirname(resolve(path)),resolve(directory));if(existsSync(path))unlinkSync(path);}
    rmdirSync(directory);
  }
});
