import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(process.argv[2] || 'source');
function edit(relative, transform) {
  const file = path.join(root, relative);
  const before = fs.readFileSync(file, 'utf8');
  const after = transform(before);
  if (after === before) throw new Error(`Nessuna modifica applicata a ${relative}`);
  fs.writeFileSync(file, after);
  console.log(`updated ${relative}`);
}

edit('frontend-react/src/components/LegacyCatalogCard.tsx', (source) => {
  source = source.replace(
    'const [favorite,setFavorite]=useState(false),[busy,setBusy]=useState(false),[galleryCover,setGalleryCover]=useState("");',
    'const [favorite,setFavorite]=useState(false),[busy,setBusy]=useState(false),[galleryCover,setGalleryCover]=useState(""),[directImageFailed,setDirectImageFailed]=useState(false);',
  );
  source = source.replace(
    'useEffect(()=>{if(directImage){setGalleryCover("");return}let alive=true;void loadBusinessImages(business.id).then((rows)=>{if(!alive)return;setGalleryCover(rows.map(imageUrlFromGallery).find(Boolean)||"")}).catch(()=>{if(alive)setGalleryCover("")});return()=>{alive=false}},[business.id,directImage]);',
    'useEffect(()=>{setDirectImageFailed(false);if(directImage){setGalleryCover("");return}let alive=true;void loadBusinessImages(business.id).then((rows)=>{if(!alive)return;setGalleryCover(rows.map(imageUrlFromGallery).find(Boolean)||"")}).catch(()=>{if(alive)setGalleryCover("")});return()=>{alive=false}},[business.id,directImage]);',
  );
  source = source.replace(
    'const category=business.subcategory||business.category||specificCategory(business), image=directImage||galleryCover;',
    'const category=business.subcategory||business.category||specificCategory(business), image=directImageFailed?galleryCover:(directImage||galleryCover);\n  const recoverBrokenCover=()=>{if(!directImage||directImageFailed)return;setDirectImageFailed(true);void loadBusinessImages(business.id).then((rows)=>setGalleryCover(rows.map(imageUrlFromGallery).find(Boolean)||"")).catch(()=>setGalleryCover(""))};',
  );
  source = source.replace(
    '<img src={image} alt={title} loading={index<2?"eager":"lazy"} fetchPriority={index<2?"high":"low"} decoding="async" />',
    '<img src={image} alt={title} loading={index<2?"eager":"lazy"} fetchPriority={index<2?"high":"low"} decoding="async" onError={recoverBrokenCover} />',
  );
  return source;
});

edit('frontend-react/src/components/BusinessCard.tsx', (source) => {
  source = source.replace(
    'const [galleryCover, setGalleryCover] = useState("");\n  const image = directImage || galleryCover;',
    'const [galleryCover, setGalleryCover] = useState("");\n  const [directImageFailed, setDirectImageFailed] = useState(false);\n  const image = directImageFailed ? galleryCover : (directImage || galleryCover);',
  );
  source = source.replace(
    'useEffect(() => {\n    if (directImage) { setGalleryCover(""); return; }',
    'useEffect(() => {\n    setDirectImageFailed(false);\n    if (directImage) { setGalleryCover(""); return; }',
  );
  source = source.replace(
    '  const toggle = async () => {',
    '  const recoverBrokenCover = () => {\n    if (!directImage || directImageFailed) return;\n    setDirectImageFailed(true);\n    void loadBusinessImages(business.id).then((rows) => {\n      setGalleryCover(rows.map(imageUrlFromGallery).find(Boolean) || "");\n    }).catch(() => setGalleryCover(""));\n  };\n\n  const toggle = async () => {',
  );
  source = source.replace(
    '              className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.02]"\n            />',
    '              className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.02]"\n              onError={recoverBrokenCover}\n            />',
  );
  return source;
});

edit('frontend-react/index.html', (source) => {
  const next = source.replace(
    /<link rel="icon"[^>]*href="[^"]+"[^>]*\/>/,
    '<link rel="icon" type="image/png" sizes="96x96" href="https://img.calabriavera.com/static/assets/images/favicon-96.png?v=20260912d" />',
  );
  if (!next.includes('favicon-96.png?v=20260912d')) throw new Error('favicon non aggiornato');
  return next;
});
