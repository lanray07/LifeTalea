import {createHash} from 'node:crypto';
import {readFileSync, existsSync} from 'node:fs';
import path from 'node:path';
import source from './dictionaries/en-GB.json';

export const allLocales = ['en-GB','en-US','en-AU','es-ES','es-419','fr-FR','fr-CA','de-DE','it-IT','pt-BR','pt-PT','nl-NL','pl-PL','sv-SE','ja-JP','hi-IN','ar','tr-TR','id-ID','ko-KR','zh-Hans','zh-Hant'] as const;
export type Locale = typeof allLocales[number];
export type Article = {title:string;summary:string;sections:{title:string;body:string}[]};
export type Dictionary = Omit<typeof source,'articles'> & {articles:Record<string,Article>};
export const preview = !process.env.SITE_URL;
const directory = path.join(process.cwd(),'src/dictionaries');
const reviewsPath = path.join(process.cwd(),'localization/reviews.json');
type Review = {status?:string;sourceHash?:string;targetHash?:string;reviewer?:string;reviewedAt?:string};
const reviews:Record<string,Review> = existsSync(reviewsPath) ? JSON.parse(readFileSync(reviewsPath,'utf8')) : {};
const digest = (value:Buffer) => createHash('sha256').update(value).digest('hex');
const sourceHash = digest(readFileSync(path.join(directory,'en-GB.json')));
function approved(locale:Locale) {
  const file=path.join(directory,`${locale}.json`);const r=reviews[locale];
  return existsSync(file) && r?.status==='APPROVED' && r.sourceHash===sourceHash && r.targetHash===digest(readFileSync(file)) && !!r.reviewer && !!r.reviewedAt;
}
// A public SITE_URL never enables pending translation drafts.
export const locales:readonly Locale[] = allLocales.filter(locale => locale==='en-GB' || (existsSync(path.join(directory,`${locale}.json`)) && (preview || approved(locale))));
export const hasLocale = (value:string):value is Locale => locales.includes(value as Locale);
const dictionaries = new Map<Locale,Dictionary>();
export function getDictionary(locale:Locale):Dictionary {
  if(!dictionaries.has(locale)) dictionaries.set(locale,JSON.parse(readFileSync(path.join(directory,`${locale}.json`),'utf8')));
  return dictionaries.get(locale)!;
}
export const direction = (locale:Locale) => locale==='ar' ? 'rtl' : 'ltr';
export function alternates(locale:Locale,slug='') {
  const suffix=slug?`${slug}/`:'';
  // Google supports ISO region codes, not numeric UN regions such as 419.
  return {canonical:`/${locale}/${suffix}`,languages:{...Object.fromEntries(locales.map(tag=>[tag==='es-419'?'es':tag,`/${tag}/${suffix}`])),'x-default':`/en-GB/${suffix}`}};
}
export function socialMetadata(locale:Locale,title:string,description:string,imageAlt:string,slug='') {
  // Open Graph requires a territory. Defaults here label social metadata;
  // they do not declare regional distribution or native linguistic approval.
  const special:Partial<Record<Locale,string>>={'ar':'ar_EG','es-419':'es_MX','zh-Hans':'zh_CN','zh-Hant':'zh_TW'};
  return {type:'website' as const,title,description,url:`/${locale}/${slug?slug+'/':''}`,siteName:'LifeTalea',locale:special[locale] || locale.replace('-','_'),images:[{url:'/hero-book.webp',alt:imageAlt}]};
}
export function languageNames() {
  return locales.map(tag=>({tag,label:new Intl.DisplayNames([tag],{type:'language'}).of(tag) || tag}));
}
