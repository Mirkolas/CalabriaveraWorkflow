import http from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { extname, join, normalize, resolve, sep } from 'node:path';

const root=resolve(process.argv[2]||'legacy/dist');
const port=Number(process.argv[3]||4190);
const physical={
  '/admin':'pages/admin/index.html',
  '/admin/attivita':'pages/admin/attivita.html',
  '/admin/recensioni':'pages/admin/recensioni.html',
  '/admin/blog':'pages/admin/blog.html',
  '/admin/impostazioni':'pages/admin/impostazioni.html',
  '/admin/utenti':'pages/admin/utenti.html',
  '/admin/categorie':'pages/admin/categorie.html',
  '/admin/comuni':'pages/admin/comuni.html',
  '/admin/messaggi':'pages/admin/messaggi.html',
  '/admin/seo':'pages/admin/seo.html',
};
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp','.jpg':'image/jpeg','.jpeg':'image/jpeg','.ico':'image/x-icon','.xml':'application/xml; charset=utf-8','.webmanifest':'application/manifest+json; charset=utf-8'};
function safe(relative){
  const cleaned=normalize(relative).replace(/^([.][.][/\\])+/, '').replace(/^[/\\]+/,'');
  const file=resolve(root,cleaned);
  if(file!==root && !file.startsWith(root+sep)) throw new Error('path escape');
  return file;
}
async function send(res,file,method){
  try{
    const info=await stat(file);if(!info.isFile())throw new Error('not file');
    const body=method==='HEAD'?null:await readFile(file);
    res.writeHead(200,{'Content-Type':mime[extname(file).toLowerCase()]||'application/octet-stream','Cache-Control':'no-store'});res.end(body);
  }catch{res.writeHead(404,{'Content-Type':'text/plain; charset=utf-8'});res.end('Not found');}
}
http.createServer(async(req,res)=>{
  try{
    const method=req.method||'GET';if(!['GET','HEAD'].includes(method)){res.writeHead(405);return res.end();}
    const u=new URL(req.url||'/',`http://${req.headers.host||'127.0.0.1'}`);
    let pathname=decodeURIComponent(u.pathname).replace(/\/+$/,'')||'/';
    // Mirror firebase.json: explicit admin pages first, then /admin/** -> admin index shell.
    if(pathname==='/admin' || pathname.startsWith('/admin/')){
      const rel=physical[pathname] || 'pages/admin/index.html';
      return send(res,safe(rel),method);
    }
    const rel=pathname.replace(/^\//,'') || 'index.html';
    return send(res,safe(rel),method);
  }catch(error){res.writeHead(500,{'Content-Type':'text/plain; charset=utf-8'});res.end(String(error?.message||error));}
}).listen(port,'127.0.0.1',()=>console.log(`Exact legacy admin oracle on http://127.0.0.1:${port}`));
