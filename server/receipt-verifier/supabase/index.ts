import {edgeHandler, productionVerifier} from './handler.mjs';

let verifier;
try {verifier=productionVerifier((name: string)=>Deno.env.get(name));} catch { /* Fail closed; never log credentials or crypto exceptions. */ }
const endpoint=Deno.env.get('SUPABASE_URL');
const serviceKey=Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
const consumeQuota=async()=>{
  if(!endpoint||!serviceKey) throw Error('Unavailable');
  const response=await fetch(endpoint+'/rest/v1/rpc/lifetalea_consume_rvs_quota',{
    method:'POST',headers:{apikey:serviceKey,authorization:'Bearer '+serviceKey,'content-type':'application/json'},
    body:'{}',redirect:'error',signal:AbortSignal.timeout(3000)
  });
  if(!response.ok) {await response.body?.cancel();throw Error('Unavailable');}
  return await response.json()===true;
};
Deno.serve(edgeHandler({verifier,consumeQuota}));
