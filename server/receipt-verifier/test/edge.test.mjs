import {test} from 'node:test';
import assert from 'node:assert/strict';
import {edgeHandler, productionVerifier, sourceQuotaSlot} from '../supabase/handler.mjs';
const url='https://example.supabase.co/functions/v1/lifetalea-receipts/v1/verify';
const request=(value,headers={'content-type':'application/json'})=>new Request(url,{method:'POST',headers,body:JSON.stringify(value)});
test('edge fails closed without secrets and never invokes quota',async()=>{
  const handler=edgeHandler({consumeQuota:()=>{throw Error('Unexpected');}});
  assert.equal((await handler(request({}))).status,503);
  assert.equal((await handler(new Request(url.replace('/v1/verify','/health')))).status,200);
  assert.throws(()=>productionVerifier(()=>undefined));
});
test('edge validates body before quota and authenticates receipts through verifier',async()=>{
  let quota=0,calls=0;
  const handler=edgeHandler({verifier:{verify:async(input)=>{calls++;assert.deepEqual(input,{userId:'user',receiptId:'receipt'});return {assertion:'signed'};}},consumeQuota:async()=>{quota++;return true;}});
  assert.equal((await handler(request({environment:'sandbox'}))).status,400);
  assert.equal((await handler(request({userId:'user',receiptId:'receipt'}))).status,200);
  assert.equal(quota,1);assert.equal(calls,1);
});
test('edge enforces shared quota, length, content type and hides internal exceptions',async()=>{
  const verifier={verify:()=>{throw Error('private secret');}};
  assert.equal((await edgeHandler({verifier,consumeQuota:async()=>false})(request({userId:'u',receiptId:'r'}))).status,429);
  const handler=edgeHandler({verifier,consumeQuota:async()=>true});
  assert.equal((await handler(request({x:'x'.repeat(2048)}))).status,413);
  assert.equal((await handler(request({}, {'content-type':'text/plain'}))).status,415);
  assert.equal((await handler(new Request(url))).status,405);
  const result=await handler(request({userId:'u',receiptId:'r'}));
  assert.equal(result.status,503);assert.equal((await result.text()).includes('private'),false);
});
test('source budget uses one bucket for an IPv6 prefix and normalizes IPv4-mapped addresses',()=>{
  const key='local-synthetic-test-key';
  assert.equal(sourceQuotaSlot('2001:db8:1:2::1',key),sourceQuotaSlot('2001:0db8:0001:0002:0000:0000:0000:0010',key));
  assert.equal(sourceQuotaSlot('192.0.2.1',key),sourceQuotaSlot('::ffff:192.0.2.1',key));
  assert.throws(()=>sourceQuotaSlot(null,key));
});

test('denied source is stopped before Amazon verification',async()=>{
  const handler=edgeHandler({verifier:{verify:async()=>assert.fail('No upstream call expected')},consumeQuota:async()=>false});
  assert.equal((await handler(request({userId:'u',receiptId:'r'}))).status,429);
});
