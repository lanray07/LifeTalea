import {createServer} from 'node:http';
import {VerificationError, receiptRequest} from './verifier.mjs';

/** Bounded, single-instance limits. A multi-instance deployment needs a shared gateway quota. */
export function createLimiter(now = () => performance.now()) {
  const clients = new Map(); let tokens = 5, updated = now();
  return ip => {
    const time = now(); tokens = Math.min(5,tokens+(time-updated)*0.005); updated=time;
    for (const [address,bucket] of clients) if (time-bucket.at > 600000) clients.delete(address);
    if (tokens < 1) return false;
    let client=clients.get(ip);
    if (!client) { if(clients.size>=1024) return false; client={tokens:5,at:time}; clients.set(ip,client); }
    client.tokens=Math.min(5,client.tokens+(time-client.at)*0.001); client.at=time;
    if(client.tokens<1) return false;
    tokens--; client.tokens--; return true;
  };
}
export function createReceiptServer(verifier, {limiter=createLimiter(), maxConcurrent=4} = {}) {
  let inFlight=0;
  const server=createServer(async (req,res)=>{
    const send=(status,value)=>{
      if(res.destroyed || res.writableEnded) return;
      res.writeHead(status,{'content-type':'application/json; charset=utf-8','cache-control':'no-store','x-content-type-options':'nosniff','content-security-policy':"default-src 'none'",...(status===429?{'retry-after':'2'}:{})});
      res.end(JSON.stringify(value));
    };
    if(req.url==='/health' && req.method==='GET') { send(200,{service:'lifetalea-amazon-rvs',version:1,ready:true,environment:verifier.environment}); return; }
    if(req.url!=='/v1/verify') { send(404,{error:'not_found'}); return; }
    if(req.method!=='POST') { send(405,{error:'method_not_allowed'}); return; }
    if(!/^application\/json(?:\s*;\s*charset=utf-8)?$/i.test(req.headers['content-type']??'')) { send(415,{error:'json_required'}); return; }
    if(!limiter(req.socket.remoteAddress ?? 'unknown') || inFlight>=maxConcurrent) { send(429,{error:'retry_later'}); return; }
    if(req.headers['content-length'] && (!/^\d+$/.test(req.headers['content-length']) || Number(req.headers['content-length'])>2048)) { send(413,{error:'request_too_large'}); return; }
    const controller=new AbortController();
    req.once('aborted',()=>controller.abort());
    res.once('close',()=>{if(!res.writableEnded) controller.abort();});
    req.setTimeout(5000,()=>req.destroy());
    inFlight++;
    try {
      const chunks=[]; let size=0;
      for await(const chunk of req) { size+=chunk.length; if(size>2048) throw new VerificationError(413,'request_too_large'); chunks.push(chunk); }
      let input;
      try { input=receiptRequest(JSON.parse(Buffer.concat(chunks).toString('utf8'))); }
      catch { throw new VerificationError(400,'invalid_request'); }
      send(200,await verifier.verify(input,controller.signal));
    } catch(error) {
      send(error instanceof VerificationError?error.status:503,{error:error instanceof VerificationError?error.code:'verification_unavailable'});
    } finally { inFlight--; }
  });
  server.headersTimeout=5000; server.requestTimeout=10000; server.keepAliveTimeout=2000; server.maxHeadersCount=32;
  return server;
}
