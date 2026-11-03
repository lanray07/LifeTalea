// Next 16.4 Windows exports can retain path separators in RSC prefetch names.
// Supply byte-identical aliases matching the client's dotted filename protocol.
const fs=require('node:fs/promises');
const path=require('node:path');
async function normalizeExport(output){
  const root=await fs.realpath(output);let copied=0;
  async function walk(directory){
    for(const entry of await fs.readdir(directory,{withFileTypes:true})){
      if(entry.isSymbolicLink())throw Error('Unexpected symlink in static export');
      const source=path.join(directory,entry.name);
      if(entry.isDirectory()){await walk(source);continue;}
      if(!entry.isFile()||!entry.name.endsWith('.txt'))continue;
      const parts=path.relative(root,source).split(path.sep);
      const start=parts.findIndex(part=>part.startsWith('__next.'));
      if(start<0||start===parts.length-1)continue; // Already flat on other platforms.
      const target=path.join(root,...parts.slice(0,start),parts.slice(start).join('.'));
      const relative=path.relative(root,target);
      if(relative.startsWith('..')||path.isAbsolute(relative))throw Error('Alias escaped static export');
      const bytes=await fs.readFile(source);
      let existing;
      try{existing=await fs.readFile(target);}catch(error){if(error.code!=='ENOENT')throw error;}
      if(existing){if(!existing.equals(bytes))throw Error(`Conflicting prefetch alias: ${relative}`);continue;}
      await fs.writeFile(target,bytes,{flag:'wx'});copied++;
    }
  }
  await walk(root);return copied;
}
module.exports={normalizeExport};
if(require.main===module)normalizeExport(path.resolve(__dirname,'../website/out')).then(count=>console.log(`Static export prefetch paths: ${count} byte-identical aliases supplied`)).catch(error=>{console.error(error);process.exitCode=1;});
