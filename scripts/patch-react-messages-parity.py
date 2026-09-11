from pathlib import Path

root = Path('source')

# Extend the shared messages data layer with the same inbox semantics used by main.
p = root / 'frontend-react/src/lib/messages.ts'
s = p.read_text(encoding='utf-8')
if 'export async function watchUnreadCounts' not in s:
    s += r'''

export type ConversationPreference = { archived?: boolean; manualUnread?: boolean; updatedAt?: number };
export type ConversationPreferences = Record<string, ConversationPreference>;
export interface PublicProfile { id: string; displayName?: string; firstName?: string; lastName?: string; avatarDataUrl?: string; [key: string]: unknown }

const preferenceKey = (uid: string) => `cv-message-prefs-v2:${uid}`;
const repliesKey = (uid: string) => `cv-message-quick-replies-v2:${uid}`;

function readLocalJson<T>(key: string, fallback: T): T {
  if (typeof localStorage === "undefined") return fallback;
  try { return JSON.parse(localStorage.getItem(key) || "null") || fallback; } catch { return fallback; }
}

export function getConversationPreferences(uid: string): ConversationPreferences {
  return readLocalJson<ConversationPreferences>(preferenceKey(uid), {});
}

export function setConversationPreference(uid: string, conversationId: string, patch: ConversationPreference) {
  const all = getConversationPreferences(uid);
  all[conversationId] = { ...(all[conversationId] || {}), ...patch, updatedAt: Date.now() };
  try { localStorage.setItem(preferenceKey(uid), JSON.stringify(all)); } catch {}
  return all;
}

export function getQuickReplies(uid: string, defaults: string[] = []) {
  const stored = readLocalJson<unknown>(repliesKey(uid), null);
  return Array.isArray(stored) && stored.length ? stored.map(String).slice(0, 8) : defaults.slice(0, 8);
}

export function saveQuickReplies(uid: string, items: string[]) {
  const normalized = items.map((value) => String(value || "").trim()).filter(Boolean).slice(0, 8);
  try { localStorage.setItem(repliesKey(uid), JSON.stringify(normalized)); } catch {}
  return normalized;
}

export async function watchUnreadCounts(uid: string, onCounts: (counts: Record<string, number>) => void, onError?: (error: unknown) => void) {
  const user = await currentUser();
  if (!user || user.uid !== uid) throw new Error("AUTH_REQUIRED");
  const { db, f } = await services();
  const query = f.query(f.collection(db, "messages"), f.where("receiverId", "==", uid), f.where("status", "==", "sent"), f.limit(300));
  return f.onSnapshot(query, (snapshot) => {
    const counts: Record<string, number> = {};
    snapshot.docs.forEach((doc) => {
      const conversationId = String(doc.data().conversationId || "");
      if (conversationId) counts[conversationId] = (counts[conversationId] || 0) + 1;
    });
    onCounts(counts);
  }, (error) => onError?.(error));
}

export async function getPublicProfile(uid: string): Promise<PublicProfile | null> {
  if (!uid) return null;
  const { db, f } = await services();
  try {
    const snapshot = await f.getDoc(f.doc(db, "publicProfiles", uid));
    return snapshot.exists() ? ({ id: snapshot.id, ...snapshot.data() } as PublicProfile) : null;
  } catch { return null; }
}

export function publicProfileName(profile: PublicProfile | null | undefined, fallback = "Utente CalabriaVera") {
  return String(profile?.displayName || [profile?.firstName, profile?.lastName].filter(Boolean).join(" ") || fallback).trim() || fallback;
}

export async function hideConversation(conversationId: string) {
  const user = await requireVerifiedUser();
  const { db, f } = await services();
  const ref = f.doc(db, "conversations", conversationId);
  const snapshot = await f.getDoc(ref);
  if (!snapshot.exists() || !(snapshot.data().participantIds || []).includes(user.uid)) throw new Error("FORBIDDEN");
  await f.updateDoc(ref, { hiddenFor: f.arrayUnion(user.uid), updatedAt: f.serverTimestamp() });
}
'''
p.write_text(s, encoding='utf-8')

# Replace the page with the full inbox experience from main, implemented in React.
p = root / 'frontend-react/src/pages/MessagesPage.tsx'
p.write_text(r'''import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import Link from "../components/Link";
import { currentUser, requireActiveUser } from "../lib/auth";
import { businessPath, loadAllBusinesses, timeValue } from "../lib/businesses";
import { startBusinessConversation } from "../lib/conversation-start";
import { languageFromPath, localizedField, withLanguage, type Language } from "../lib/language";
import {
  getConversationPreferences, getPublicProfile, getQuickReplies, hideConversation, listConversations,
  markConversationRead, publicProfileName, saveQuickReplies, sendConversationMessage, setConversationPreference,
  watchConversations, watchMessages, watchUnreadCounts,
  type Conversation, type ConversationPreferences, type Message, type PublicProfile,
} from "../lib/messages";
import { navigate } from "../lib/navigation";
import { setPageSeo } from "../lib/seo";
import type { Business } from "../types";

const LOCALES: Record<Language, string> = { it: "it-IT", en: "en-GB", fr: "fr-FR", de: "de-DE", es: "es-ES" };
type Filter = "all" | "unread" | "archived";
const COPY: Record<Language, Record<string, string | string[]>> = {
  it: { account:"Account",title:"Messaggi",inbox:"Inbox",loadError:"Impossibile caricare i messaggi.",verify:"Verifica prima il tuo indirizzo email.",openError:"Impossibile aprire questa conversazione.",sendVerify:"Verifica la tua email prima di inviare messaggi.",sendError:"Messaggio non inviato. Riprova.",conversations:"Conversazioni",conversation:"Conversazione",newConversation:"Nuova conversazione",none:"Nessuna conversazione",select:"Seleziona una conversazione",first:"Inizia la conversazione.",open:"Apri una conversazione dalla lista.",message:"Messaggio",placeholder:"Scrivi un messaggio…",send:"Invia",business:"Attività",search:"Cerca conversazioni",all:"Tutte",unread:"Non lette",archived:"Archiviate",archive:"Archivia",restore:"Ripristina",delete:"Elimina chat",confirmDelete:"Eliminare questa chat dalla tua inbox?",markUnread:"Segna non letta",openBusiness:"Apri scheda",quickReplies:"Risposte rapide",editReplies:"Modifica",saveReplies:"Salva",cancel:"Annulla",editHint:"Massimo 8 risposte, una per riga.",user:"Utente CalabriaVera",owner:"Proprietario attività",quickDefault:["Grazie per averci contattato.","Siamo disponibili, scrivici pure maggiori dettagli.","Puoi trovare tutte le informazioni aggiornate nella nostra scheda."] },
  en: { account:"Account",title:"Messages",inbox:"Inbox",loadError:"Unable to load messages.",verify:"Verify your email address first.",openError:"Unable to open this conversation.",sendVerify:"Verify your email before sending messages.",sendError:"Message not sent. Try again.",conversations:"Conversations",conversation:"Conversation",newConversation:"New conversation",none:"No conversations",select:"Select a conversation",first:"Start the conversation.",open:"Open a conversation from the list.",message:"Message",placeholder:"Write a message…",send:"Send",business:"Business",search:"Search conversations",all:"All",unread:"Unread",archived:"Archived",archive:"Archive",restore:"Restore",delete:"Delete chat",confirmDelete:"Delete this chat from your inbox?",markUnread:"Mark unread",openBusiness:"Open profile",quickReplies:"Quick replies",editReplies:"Edit",saveReplies:"Save",cancel:"Cancel",editHint:"Maximum 8 replies, one per line.",user:"CalabriaVera user",owner:"Business owner",quickDefault:["Thanks for contacting us.","We are available; feel free to send more details.","You can find all updated information on our profile."] },
  fr: { account:"Compte",title:"Messages",inbox:"Boîte de réception",loadError:"Impossible de charger les messages.",verify:"Vérifiez d’abord votre adresse e-mail.",openError:"Impossible d’ouvrir cette conversation.",sendVerify:"Vérifiez votre e-mail avant d’envoyer des messages.",sendError:"Message non envoyé. Réessayez.",conversations:"Conversations",conversation:"Conversation",newConversation:"Nouvelle conversation",none:"Aucune conversation",select:"Sélectionnez une conversation",first:"Commencez la conversation.",open:"Ouvrez une conversation dans la liste.",message:"Message",placeholder:"Écrivez un message…",send:"Envoyer",business:"Activité",search:"Rechercher une conversation",all:"Toutes",unread:"Non lues",archived:"Archivées",archive:"Archiver",restore:"Restaurer",delete:"Supprimer la discussion",confirmDelete:"Supprimer cette discussion de votre boîte de réception ?",markUnread:"Marquer comme non lue",openBusiness:"Ouvrir la fiche",quickReplies:"Réponses rapides",editReplies:"Modifier",saveReplies:"Enregistrer",cancel:"Annuler",editHint:"8 maximum, une par ligne.",user:"Utilisateur CalabriaVera",owner:"Propriétaire de l’activité",quickDefault:["Merci de nous avoir contactés.","Nous sommes disponibles, envoyez-nous plus de détails.","Vous trouverez toutes les informations à jour sur notre fiche."] },
  de: { account:"Konto",title:"Nachrichten",inbox:"Posteingang",loadError:"Nachrichten konnten nicht geladen werden.",verify:"Bestätige zuerst deine E-Mail-Adresse.",openError:"Diese Unterhaltung konnte nicht geöffnet werden.",sendVerify:"Bestätige deine E-Mail, bevor du Nachrichten sendest.",sendError:"Nachricht nicht gesendet. Versuche es erneut.",conversations:"Unterhaltungen",conversation:"Unterhaltung",newConversation:"Neue Unterhaltung",none:"Keine Unterhaltungen",select:"Wähle eine Unterhaltung",first:"Unterhaltung beginnen.",open:"Öffne eine Unterhaltung aus der Liste.",message:"Nachricht",placeholder:"Nachricht schreiben…",send:"Senden",business:"Betrieb",search:"Unterhaltungen durchsuchen",all:"Alle",unread:"Ungelesen",archived:"Archiviert",archive:"Archivieren",restore:"Wiederherstellen",delete:"Chat löschen",confirmDelete:"Diesen Chat aus deinem Posteingang löschen?",markUnread:"Als ungelesen markieren",openBusiness:"Profil öffnen",quickReplies:"Schnellantworten",editReplies:"Bearbeiten",saveReplies:"Speichern",cancel:"Abbrechen",editHint:"Höchstens 8, eine pro Zeile.",user:"CalabriaVera-Nutzer",owner:"Betriebsinhaber",quickDefault:["Danke für deine Nachricht.","Wir sind erreichbar; sende uns gerne weitere Details.","Alle aktuellen Informationen findest du in unserem Profil."] },
  es: { account:"Cuenta",title:"Mensajes",inbox:"Bandeja de entrada",loadError:"No se pudieron cargar los mensajes.",verify:"Verifica primero tu correo electrónico.",openError:"No se pudo abrir esta conversación.",sendVerify:"Verifica tu correo antes de enviar mensajes.",sendError:"Mensaje no enviado. Inténtalo de nuevo.",conversations:"Conversaciones",conversation:"Conversación",newConversation:"Nueva conversación",none:"No hay conversaciones",select:"Selecciona una conversación",first:"Inicia la conversación.",open:"Abre una conversación de la lista.",message:"Mensaje",placeholder:"Escribe un mensaje…",send:"Enviar",business:"Actividad",search:"Buscar conversaciones",all:"Todas",unread:"No leídas",archived:"Archivadas",archive:"Archivar",restore:"Restaurar",delete:"Eliminar chat",confirmDelete:"¿Eliminar este chat de tu bandeja de entrada?",markUnread:"Marcar como no leído",openBusiness:"Abrir ficha",quickReplies:"Respuestas rápidas",editReplies:"Editar",saveReplies:"Guardar",cancel:"Cancelar",editHint:"Máximo 8, una por línea.",user:"Usuario de CalabriaVera",owner:"Propietario del negocio",quickDefault:["Gracias por contactar con nosotros.","Estamos disponibles; envíanos más detalles.","Encontrarás toda la información actualizada en nuestra ficha."] },
};

function c(copy: Record<string, string | string[]>, key: string) { return String(copy[key] || key); }
function formatTime(value: unknown, language: Language) { const stamp=timeValue(value); return stamp ? new Intl.DateTimeFormat(LOCALES[language],{dateStyle:"short",timeStyle:"short"}).format(stamp) : ""; }
function peerId(row: Conversation, uid: string) { return (row.participantIds || []).find((id) => id !== uid) || ""; }
function Avatar({ profile, name }: { profile?: PublicProfile | null; name: string }) { const src=String(profile?.avatarDataUrl||""); return <span className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-full bg-stone-200 text-sm font-black text-stone-600">{src ? <img src={src} alt="" className="h-full w-full object-cover" /> : String(name||"U").trim().charAt(0).toUpperCase()}</span>; }

export default function MessagesPage() {
  const language=languageFromPath(), copy=COPY[language];
  const [userId,setUserId]=useState("");
  const [conversations,setConversations]=useState<Conversation[]|null>(null);
  const [selectedId,setSelectedId]=useState("");
  const [messages,setMessages]=useState<Message[]|null>(null);
  const [businesses,setBusinesses]=useState<Record<string,Business>>({});
  const [profiles,setProfiles]=useState<Record<string,PublicProfile|null>>({});
  const [unreadCounts,setUnreadCounts]=useState<Record<string,number>>({});
  const [preferences,setPreferences]=useState<ConversationPreferences>({});
  const [quickReplies,setQuickReplies]=useState<string[]>([]);
  const [editingReplies,setEditingReplies]=useState(false);
  const [replyDraft,setReplyDraft]=useState("");
  const [search,setSearch]=useState("");
  const [filter,setFilter]=useState<Filter>("all");
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");

  useEffect(()=>{
    setPageSeo({title:`${c(copy,"title")} | CalabriaVera`,description:c(copy,"title"),path:"/messaggi",robots:"noindex,nofollow"});
    let active=true;
    void (async()=>{
      try {
        const current=await currentUser(); if(!current){navigate(withLanguage("/login?next=/messaggi",language),true);return;}
        const user=await requireActiveUser(current); if(!active)return;
        setUserId(user.uid); setPreferences(getConversationPreferences(user.uid));
        const defaults=(copy.quickDefault as string[])||[]; const replies=getQuickReplies(user.uid,defaults); setQuickReplies(replies); setReplyDraft(replies.join("\n"));
        const [rows,allBusinesses]=await Promise.all([listConversations(),loadAllBusinesses().catch(()=>[])]);
        const map=Object.fromEntries(allBusinesses.map((business)=>[business.id,business])); setBusinesses(map);
        let nextRows=rows; const params=new URLSearchParams(location.search); const businessId=params.get("business")||"", ownerId=params.get("owner")||"";
        if(businessId&&ownerId&&ownerId!==user.uid){const started=await startBusinessConversation(businessId,ownerId);nextRows=[started,...rows.filter((row)=>row.id!==started.id)];history.replaceState({},"",withLanguage(`/messaggi?conversation=${encodeURIComponent(started.id)}`,language));}
        if(!active)return; setConversations(nextRows);
        const requested=new URLSearchParams(location.search).get("conversation")||""; setSelectedId(requested&&nextRows.some((row)=>row.id===requested)?requested:nextRows[0]?.id||"");
      } catch(cause){if(!active)return;const code=cause instanceof Error?cause.message:"";if(code==="AUTH_REQUIRED"||code==="ACCOUNT_SUSPENDED"){navigate(withLanguage(code==="ACCOUNT_SUSPENDED"?"/login?suspended=1":"/login?next=/messaggi",language),true);return;}setError(code==="EMAIL_NOT_VERIFIED"?c(copy,"verify"):c(copy,"loadError"));}
    })();
    return()=>{active=false};
  },[language]);

  useEffect(()=>{if(!userId)return;let alive=true,stop:(()=>void)|undefined;void watchConversations((rows)=>{if(!alive)return;setConversations(rows);setSelectedId((current)=>current&&rows.some((row)=>row.id===current)?current:rows[0]?.id||"");},()=>{if(alive)setError(c(copy,"loadError"));}).then((u)=>{if(alive)stop=u;else u();}).catch(()=>{if(alive)setError(c(copy,"loadError"));});return()=>{alive=false;stop?.()};},[userId,language]);
  useEffect(()=>{if(!userId)return;let alive=true,stop:(()=>void)|undefined;void watchUnreadCounts(userId,(counts)=>{if(alive)setUnreadCounts(counts);},()=>undefined).then((u)=>{if(alive)stop=u;else u();}).catch(()=>undefined);return()=>{alive=false;stop?.()};},[userId]);

  useEffect(()=>{if(!userId||!conversations?.length)return;let active=true;const ids=[...new Set(conversations.map((row)=>peerId(row,userId)).filter(Boolean))];void Promise.all(ids.map(async(id)=>[id,await getPublicProfile(id)] as const)).then((pairs)=>{if(active)setProfiles((current)=>({...current,...Object.fromEntries(pairs)}));});return()=>{active=false};},[conversations,userId]);

  const selected=useMemo(()=>conversations?.find((row)=>row.id===selectedId)||null,[conversations,selectedId]);
  useEffect(()=>{if(!selectedId){setMessages([]);return;}let active=true,stop:(()=>void)|undefined;setMessages(null);void watchMessages(selectedId,(rows)=>{if(!active)return;setMessages(rows);void markConversationRead(rows).catch(()=>undefined);},()=>{if(active){setMessages([]);setError(c(copy,"openError"));}}).then((u)=>{if(active)stop=u;else u();}).catch(()=>{if(active){setMessages([]);setError(c(copy,"openError"));}});return()=>{active=false;stop?.()};},[selectedId,language]);

  const nameFor=(row:Conversation)=>{const peer=peerId(row,userId),business=businesses[String(row.businessId||"")];return publicProfileName(profiles[peer],business?.ownerId===peer?c(copy,"owner"):c(copy,"user"));};
  const unreadFor=(row:Conversation)=>Math.max(Number(unreadCounts[row.id]||0),preferences[row.id]?.manualUnread?1:0);
  const visible=useMemo(()=>{const q=search.trim().toLowerCase();return (conversations||[]).filter((row)=>{const archived=preferences[row.id]?.archived===true;if(filter==="archived"&&!archived)return false;if(filter!=="archived"&&archived)return false;if(filter==="unread"&&unreadFor(row)===0)return false;if(!q)return true;const business=businesses[String(row.businessId||"")];return [nameFor(row),business?.name,row.lastMessage].join(" ").toLowerCase().includes(q);});},[conversations,preferences,filter,search,businesses,profiles,unreadCounts,userId]);

  const choose=(row:Conversation)=>{if(userId){setPreferences(setConversationPreference(userId,row.id,{manualUnread:false}));}setSelectedId(row.id);history.replaceState({},"",withLanguage(`/messaggi?conversation=${encodeURIComponent(row.id)}`,language));};
  const archive=(row:Conversation)=>{if(!userId)return;const next=!(preferences[row.id]?.archived===true);setPreferences(setConversationPreference(userId,row.id,{archived:next}));if(next&&selectedId===row.id)setSelectedId("");};
  const remove=async(row:Conversation)=>{if(!window.confirm(c(copy,"confirmDelete")))return;try{await hideConversation(row.id);setConversations((current)=>current?.filter((item)=>item.id!==row.id)||[]);if(selectedId===row.id){setSelectedId("");setMessages([]);}}catch{setError(c(copy,"loadError"));}};
  const markUnread=()=>{if(!selected||!userId)return;setPreferences(setConversationPreference(userId,selected.id,{manualUnread:true}));};
  const saveReplies=()=>{if(!userId)return;const saved=saveQuickReplies(userId,replyDraft.split(/\r?\n/));setQuickReplies(saved);setReplyDraft(saved.join("\n"));setEditingReplies(false);};
  const applyQuick=(value:string)=>{const field=document.getElementById("message-text") as HTMLTextAreaElement|null;if(!field)return;field.value=value;field.focus();};

  const submit=async(event:FormEvent<HTMLFormElement>)=>{event.preventDefault();if(!selected)return;const form=event.currentTarget,data=new FormData(form),text=String(data.get("message")||"").trim();if(!text)return;setBusy(true);setError("");try{await sendConversationMessage(selected,text);form.reset();setConversations((current)=>current?.map((row)=>row.id===selected.id?{...row,lastMessage:text,updatedAt:Date.now(),lastSenderId:userId}:row)||current);}catch(cause){const code=cause instanceof Error?cause.message:"";setError(code==="EMAIL_NOT_VERIFIED"?c(copy,"sendVerify"):c(copy,"sendError"));}finally{setBusy(false);}};

  const selectedBusiness=selected?businesses[String(selected.businessId||"")]:undefined, selectedPeer=selected?peerId(selected,userId):"", selectedName=selected?nameFor(selected):c(copy,"select");
  return <section className="mx-auto max-w-7xl px-5 py-10 lg:px-8 lg:py-14">
    <p className="text-xs font-black uppercase tracking-[.16em] text-emerald-700">{c(copy,"inbox")}</p><h1 className="mt-2 text-4xl font-black tracking-[-.04em]">{c(copy,"title")}</h1>
    {error?<div className="mt-5 rounded-xl bg-red-50 p-4 text-sm font-bold text-red-800">{error}</div>:null}
    <div className="mt-7 grid min-h-[650px] overflow-hidden rounded-[1.7rem] border border-stone-200 bg-white lg:grid-cols-[350px_1fr]">
      <aside className="border-b border-stone-200 lg:border-b-0 lg:border-r"><div className="border-b border-stone-200 p-4"><div className="flex items-center justify-between"><strong>{c(copy,"conversations")}</strong><span className="rounded-full bg-stone-100 px-2 py-1 text-xs font-black">{visible.length}</span></div><input type="search" value={search} onChange={(e)=>setSearch(e.target.value)} placeholder={c(copy,"search")} className="mt-3 w-full rounded-xl border border-stone-200 bg-stone-50 px-3 py-2.5 text-sm"/><div className="mt-3 flex gap-1 rounded-xl bg-stone-100 p-1">{(["all","unread","archived"] as Filter[]).map((value)=><button key={value} type="button" onClick={()=>setFilter(value)} className={`flex-1 rounded-lg px-2 py-2 text-xs font-black ${filter===value?"bg-white shadow-sm":"text-stone-500"}`}>{c(copy,value)}</button>)}</div></div>
        <div className="max-h-[420px] overflow-y-auto lg:max-h-[560px]">{conversations===null?<div className="p-4"><div className="h-20 animate-pulse rounded-xl bg-stone-100"/></div>:visible.length?visible.map((row)=>{const peer=peerId(row,userId),business=businesses[String(row.businessId||"")],unread=unreadFor(row);return <div key={row.id} className={`border-b border-stone-100 ${selectedId===row.id?"bg-emerald-50":""}`}><button type="button" onClick={()=>choose(row)} className="flex w-full gap-3 p-4 text-left"><Avatar profile={profiles[peer]} name={nameFor(row)}/><span className="min-w-0 flex-1"><span className="flex items-center justify-between gap-2"><strong className="truncate text-sm">{nameFor(row)}</strong><small className="shrink-0 text-[10px] text-stone-400">{formatTime(row.updatedAt,language)}</small></span><span className="mt-0.5 block truncate text-xs font-bold text-emerald-800">{localizedField<string>(business||{},"name",language)||business?.name||c(copy,"business")}</span><span className="mt-1 block truncate text-xs text-stone-500">{String(row.lastMessage||c(copy,"newConversation"))}</span></span>{unread?<span className="min-w-5 rounded-full bg-emerald-700 px-1.5 text-center text-[10px] font-black leading-5 text-white">{unread>99?"99+":unread}</span>:null}</button><div className="flex justify-end gap-3 px-4 pb-3 text-[11px] font-black"><button type="button" onClick={()=>archive(row)} className="text-stone-500">{preferences[row.id]?.archived?c(copy,"restore"):c(copy,"archive")}</button><button type="button" onClick={()=>void remove(row)} className="text-red-700">{c(copy,"delete")}</button></div></div>}):<p className="p-5 text-sm text-stone-500">{c(copy,"none")}</p>}</div>
      </aside>
      <div className="flex min-h-[560px] flex-col"><div className="flex flex-wrap items-center justify-between gap-3 border-b border-stone-200 p-4">{selected?<div className="flex items-center gap-3"><Avatar profile={profiles[selectedPeer]} name={selectedName}/><div><strong className="block">{selectedName}</strong><span className="text-xs text-stone-500">{localizedField<string>(selectedBusiness||{},"name",language)||selectedBusiness?.name||c(copy,"business")}</span></div></div>:<strong>{c(copy,"select")}</strong>}{selected?<div className="flex flex-wrap gap-3 text-xs font-black"><button type="button" onClick={markUnread}>{c(copy,"markUnread")}</button><button type="button" onClick={()=>archive(selected)}>{preferences[selected.id]?.archived?c(copy,"restore"):c(copy,"archive")}</button>{selectedBusiness?<Link href={withLanguage(businessPath(selectedBusiness),language)} className="text-emerald-800">{c(copy,"openBusiness")}</Link>:null}</div>:null}</div>
        <div className="flex-1 space-y-3 overflow-y-auto bg-stone-50 p-4 sm:p-6">{messages===null?<div className="h-16 w-2/3 animate-pulse rounded-2xl bg-stone-200"/>:messages.length?messages.map((message)=>{const mine=message.senderId===userId;return <div key={message.id} className={`flex max-w-[88%] items-end gap-2 ${mine?"ml-auto flex-row-reverse":""}`}>{!mine?<Avatar profile={profiles[selectedPeer]} name={selectedName}/>:null}<div className={`rounded-2xl px-4 py-3 ${mine?"bg-emerald-700 text-white":"bg-white text-stone-800 shadow-sm"}`}><p className="whitespace-pre-wrap text-sm leading-6">{message.text}</p><span className={`mt-1 flex items-center justify-end gap-2 text-[11px] ${mine?"text-emerald-100":"text-stone-400"}`}>{formatTime(message.createdAt,language)}{mine?<span aria-label={message.readAt?"Letto":"Inviato"}>{message.readAt?"✓✓":"✓"}</span>:null}</span></div></div>}):<p className="text-sm text-stone-500">{selected?c(copy,"first"):c(copy,"open")}</p>}</div>
        {selected?<div className="border-t border-stone-200 bg-white">{editingReplies?<div className="border-b border-stone-100 p-4"><label className="text-xs font-black">{c(copy,"quickReplies")}<textarea value={replyDraft} onChange={(e)=>setReplyDraft(e.target.value)} rows={4} className="mt-2 w-full rounded-xl border border-stone-200 p-3 text-sm"/></label><p className="mt-1 text-xs text-stone-400">{c(copy,"editHint")}</p><div className="mt-2 flex gap-2"><button type="button" onClick={saveReplies} className="rounded-lg bg-stone-950 px-3 py-2 text-xs font-black text-white">{c(copy,"saveReplies")}</button><button type="button" onClick={()=>setEditingReplies(false)} className="rounded-lg border border-stone-200 px-3 py-2 text-xs font-black">{c(copy,"cancel")}</button></div></div>:<div className="flex flex-wrap items-center gap-2 border-b border-stone-100 px-4 py-3"><strong className="mr-1 text-xs">{c(copy,"quickReplies")}</strong>{quickReplies.map((reply,index)=><button key={`${index}-${reply}`} type="button" onClick={()=>applyQuick(reply)} className="max-w-[220px] truncate rounded-full bg-stone-100 px-3 py-1.5 text-xs font-bold">{reply}</button>)}<button type="button" onClick={()=>setEditingReplies(true)} className="ml-auto text-xs font-black text-emerald-800">{c(copy,"editReplies")}</button></div>}<form onSubmit={submit} className="flex gap-2 p-3 sm:p-4"><label className="sr-only" htmlFor="message-text">{c(copy,"message")}</label><textarea id="message-text" name="message" required maxLength={2000} rows={2} placeholder={c(copy,"placeholder")} className="min-h-12 flex-1 resize-none rounded-xl border border-stone-200 bg-stone-50 px-3 py-3 outline-none focus:border-emerald-600"/><button disabled={busy} className="self-end rounded-xl bg-stone-950 px-5 py-3 text-sm font-black text-white disabled:opacity-50">{c(copy,"send")}</button></form></div>:null}
      </div>
    </div>
  </section>;
}
''', encoding='utf-8')

print('React messages parity patch applied')
