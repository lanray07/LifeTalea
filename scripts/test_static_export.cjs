const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const os=require('node:os');
const path=require('node:path');
const {normalizeExport}=require('./normalize_static_export.cjs');
(async()=>{
  const temporaryRoot=await fs.realpath(os.tmpdir());
  const fixture=await fs.mkdtemp(path.join(temporaryRoot,'lifetalea-export-fixture-'));
  try{
    const route=path.join(fixture,'fr-FR','features');
    const nested=path.join(route,'__next.!KGxvY2FsaXplZCk','$d$locale','$d$slug');
    await fs.mkdir(nested,{recursive:true});
    const payload=Buffer.from('0:{"locale":"fr-FR","message":"Souvenirs"}\n');
    await fs.writeFile(path.join(nested,'__PAGE__.txt'),payload);
    await fs.writeFile(path.join(route,'index.html'),'<h1>Souvenirs</h1>');
    const requested=path.join(route,'__next.!KGxvY2FsaXplZCk.$d$locale.$d$slug.__PAGE__.txt');
    assert.equal(await normalizeExport(fixture),1);
    assert.deepEqual(await fs.readFile(requested),payload);
    assert.equal(await normalizeExport(fixture),0);
    assert.equal(await fs.readFile(path.join(route,'index.html'),'utf8'),'<h1>Souvenirs</h1>');
    await fs.writeFile(requested,'conflicting payload');
    await assert.rejects(normalizeExport(fixture),/Conflicting prefetch alias/);
    console.log('Static-export regression: exact browser-request filename, payload preservation, idempotence, HTML preservation and conflict refusal passed');
  }finally{
    const resolved=await fs.realpath(fixture);
    if(path.dirname(resolved)!==temporaryRoot||!path.basename(resolved).startsWith('lifetalea-export-fixture-'))throw Error('Unsafe fixture cleanup target');
    await fs.rm(resolved,{recursive:true,force:true});
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
