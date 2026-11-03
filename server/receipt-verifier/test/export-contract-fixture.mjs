// Offline interoperability fixture only. The ephemeral private key is never written.
import {generateKeyPairSync} from 'node:crypto';
import {writeFileSync} from 'node:fs';
import {createVerifier,SKU} from '../src/verifier.mjs';
const {privateKey}=generateKeyPairSync('rsa',{modulusLength:2048});
const key=privateKey.export({type:'pkcs8',format:'pem'});
const now=1700000000000, request={userId:'fixture-user',receiptId:'fixture-receipt'};
const receipt={receiptId:request.receiptId,productId:SKU,productType:'ENTITLED',cancelDate:null,purchaseDate:now-1000,betaProduct:false,testTransaction:false};
const factory=(environment,override={})=>createVerifier({environment,sharedSecret:'offline-contract-fixture',privateKey:key,ttlMs:3600000},async()=>new Response(JSON.stringify({...receipt,...override})),()=>now);
const production=factory('production');
const fixture={provenance:'OFFLINE_CONTRACT_FIXTURE_NOT_AN_AMAZON_TRANSACTION',now,...request,publicKey:production.publicKey,active:(await production.verify(request)).assertion,canceled:(await factory('production',{cancelDate:now}).verify(request)).assertion,sandbox:(await factory('sandbox',{testTransaction:true}).verify(request)).assertion};
writeFileSync(new URL('../../../android/app/src/androidTest/assets/rvs-contract.json',import.meta.url),JSON.stringify(fixture,null,2)+'\n');
process.stdout.write('Wrote public signed Node/Android interoperability fixtures; no private key retained.\n');
