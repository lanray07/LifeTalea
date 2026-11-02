import type {Metadata} from 'next';
import Link from 'next/link';
import {notFound} from 'next/navigation';
import {articles,siteUrl} from '../../../content';
type Props={params:Promise<{locale:string;slug:string}>};
export const dynamicParams=false;
export function generateStaticParams(){return Object.keys(articles).map(slug=>({locale:'en-GB',slug}))}
export async function generateMetadata({params}:Props):Promise<Metadata>{const {slug}=await params; const a=articles[slug]; return a?{title:a.title,description:a.summary,alternates:{canonical:`/en-GB/${slug}/`,languages:{'en-GB':`/en-GB/${slug}/`,'x-default':`/en-GB/${slug}/`}}}:{};}
export default async function Page({params}:Props){const {locale,slug}=await params;const a=articles[slug];if(locale!=='en-GB'||!a)notFound();const breadcrumb={'@context':'https://schema.org','@type':'BreadcrumbList',itemListElement:[{'@type':'ListItem',position:1,name:'LifeTalea',item:`${siteUrl}/en-GB/`},{'@type':'ListItem',position:2,name:a.title,item:`${siteUrl}/en-GB/${slug}/`}]};return <main id="main" className="article"><script type="application/ld+json" dangerouslySetInnerHTML={{__html:JSON.stringify(breadcrumb).replace(/</g,'\\u003c')}}/><Link href="/en-GB/" className="back">← LifeTalea</Link><h1>{a.title}</h1><p className="intro">{a.summary}</p>{a.sections.map(s=><section key={s.title}><h2>{s.title}</h2><p>{s.body}</p></section>)}<aside><h2>Explore the next chapter</h2><div className="related">{Object.entries(articles).filter(([key])=>key!==slug).map(([key,value])=><Link href={`/en-GB/${key}/`} key={key}>{value.title}</Link>)}</div></aside></main>}
