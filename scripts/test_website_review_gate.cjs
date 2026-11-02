const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const crypto=require('node:crypto');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
const ts=require(path.join(root,'website/node_modules/typescript'));
const source=fs.readFileSync(path.join(root,'website/src/i18n.ts'),'utf8');
const compiled=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,esModuleInterop:true}}).outputText;
const dictionary=tag=>path.join(root,`website/src/dictionaries/${tag}.json`);
const digest=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
function evaluate({preview=false,record=null,changedTarget=false}={}) {
  const exportsObject={};
  const mockedFs={...fs,readFileSync(file,...args){
    if(String(file).endsWith(path.join('localization','reviews.json')) && record)return JSON.stringify({'fr-FR':record});
    const bytes=fs.readFileSync(file,...args);
    if(changedTarget && String(file)===dictionary('fr-FR'))return Buffer.concat([Buffer.from(bytes),Buffer.from(' ')]);
    return bytes;
  }};
  const load=name=>name==='node:fs'?mockedFs:name.startsWith('.')?require(path.join(root,'website/src',name)):require(name);
  vm.runInNewContext(compiled,{exports:exportsObject,require:load,process:{cwd:()=>path.join(root,'website'),env:preview?{}:{SITE_URL:'https://example.com'}}});
  return Array.from(exportsObject.locales);
}
assert.deepEqual(evaluate(),['en-GB']);
assert.equal(evaluate({preview:true}).length,22);
const fixture={status:'APPROVED',sourceHash:digest(fs.readFileSync(dictionary('en-GB'))),targetHash:digest(fs.readFileSync(dictionary('fr-FR'))),reviewer:'Test fixture only',reviewedAt:'Test fixture only'};
assert.deepEqual(evaluate({record:fixture}),['en-GB','fr-FR']);
assert.deepEqual(evaluate({record:fixture,changedTarget:true}),['en-GB']);
assert.deepEqual(evaluate({record:{...fixture,sourceHash:'outdated'}}),['en-GB']);
assert.deepEqual(evaluate({record:{...fixture,reviewer:''}}),['en-GB']);
console.log('6 website review-gate cases passed; real review files unchanged');
