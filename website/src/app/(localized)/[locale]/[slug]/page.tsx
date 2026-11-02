import type {Metadata} from 'next';
import Link from 'next/link';
import {notFound} from 'next/navigation';
import {articles,siteUrl} from '../../../../content';
import {hasLocale,getDictionary,alternates,socialMetadata} from '../../../../i18n';
type Props={params:Promise<{locale:string;slug:string}>};
export const dynamicParams=false;
export function generateStaticParams(){return Object.keys(articles).map(slug=>({slug}));}
export async function generateMetadata({params}:Props):Promise<Metadata>{const {locale,slug}=await params;if(!hasLocale(locale))return {};const d=getDictionary(locale);const a=d.articles[slug];return a?{title:a.title,description:a.summary,alternates:alternates(locale,slug),openGraph:socialMetadata(locale,a.title,a.summary,d.home.imageAlt,slug)}:{};}
export default async function Page({params}:Props){const {locale,slug}=await params;if(!hasLocale(locale))notFound();const d=getDictionary(locale);const a=d.articles[slug];if(!a)notFound();const breadcrumb={'@context':'https://schema.org','@type':'BreadcrumbList',inLanguage:locale,itemListElement:[{'@type':'ListItem',position:1,name:'LifeTalea',item:`${siteUrl}/${locale}/`},{'@type':'ListItem',position:2,name:a.title,item:`${siteUrl}/${locale}/${slug}/`}]};return <main id="main" className="article"><script type="application/ld+json" dangerouslySetInnerHTML={{__html:JSON.stringify(breadcrumb).replace(/</g,'\\u003c')}}/><Link href={`/${locale}/`} className="back"><span className="direction-arrow" aria-hidden="true">←</span> LifeTalea</Link><h1>{a.title}</h1><p className="intro">{a.summary}</p>{a.sections.map((s,index)=><section key={index}><h2>{s.title}</h2><p>{s.body}</p></section>)}<aside><h2>{d.ui.related}</h2><div className="related">{Object.entries(d.articles).filter(([key])=>key!==slug).map(([key,value])=><Link href={`/${locale}/${key}/`} key={key}>{value.title}</Link>)}</div></aside></main>;}
