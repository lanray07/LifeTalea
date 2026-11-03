import {readFileSync} from 'node:fs';
import {createVerifier} from './verifier.mjs';
import {createReceiptServer} from './http.mjs';

try {
  if(process.env.NODE_TLS_REJECT_UNAUTHORIZED === '0') throw Error('Insecure TLS configuration is forbidden');
  const environment=process.env.RVS_ENVIRONMENT;
  const sharedSecret=process.env.AMAZON_SHARED_SECRET;
  if(!['production','sandbox'].includes(environment) || !sharedSecret || (environment==='production' && sharedSecret.length<16)) throw Error('Configure RVS_ENVIRONMENT and AMAZON_SHARED_SECRET in server secrets');
  const file=process.env.RVS_SIGNING_PRIVATE_KEY_FILE;
  const b64=process.env.RVS_SIGNING_PRIVATE_KEY_PEM_B64;
  if(Boolean(file)===Boolean(b64)) throw Error('Configure exactly one server signing-key source');
  const privateKey=file?readFileSync(file):Buffer.from(b64,'base64');
  const allow=process.env.ALLOW_AMAZON_TEST_TRANSACTIONS ?? 'false';
  if(!['true','false'].includes(allow)) throw Error('Invalid ALLOW_AMAZON_TEST_TRANSACTIONS');
  const verifier=createVerifier({environment,sharedSecret,privateKey,ttlMs:6*60*60*1000,allowAmazonTestTransactions:allow==='true'});
  const port=Number(process.env.PORT ?? 8080), host=process.env.HOST ?? '127.0.0.1';
  if(!Number.isInteger(port) || port<1 || port>65535 || !['127.0.0.1','0.0.0.0'].includes(host)) throw Error('Invalid bind configuration');
  const server=createReceiptServer(verifier);
  server.listen(port,host,()=>process.stdout.write(`LifeTalea receipt verifier listening (${environment}); TLS termination required outside localhost\n`));
  for(const signal of ['SIGTERM','SIGINT']) process.once(signal,()=>{server.close();server.closeAllConnections();});
} catch {
  // Config errors must never print a private PEM, shared secret or their upstream URL.
  process.stderr.write('Receipt verifier configuration failed. Check the documented server-only environment variables.\n');
  process.exitCode=1;
}
