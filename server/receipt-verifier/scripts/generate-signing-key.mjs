import {generateKeyPairSync,createHash} from 'node:crypto';
import {writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const [privatePath,publicPath]=process.argv.slice(2);
if(!privatePath?.endsWith('.private.pem') || !publicPath || resolve(privatePath)===resolve(publicPath)) {
  process.stderr.write('Usage: node generate-signing-key.mjs <outside-repo/name.private.pem> <public-key.b64>\n');process.exitCode=1;
} else {
  const {privateKey,publicKey}=generateKeyPairSync('rsa',{modulusLength:3072});
  const publicDer=publicKey.export({type:'spki',format:'der'});
  // Exclusive creation prevents accidental replacement of an existing signing identity.
  writeFileSync(privatePath,privateKey.export({type:'pkcs8',format:'pem'}),{flag:'wx',mode:0o600});
  writeFileSync(publicPath,publicDer.toString('base64')+'\n',{flag:'wx',mode:0o644});
  process.stdout.write('Created signing files. Public-key SHA-256: '+createHash('sha256').update(publicDer).digest('hex')+'\n');
}
