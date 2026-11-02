import Link from 'next/link';
import {listingUrl,siteUrl,publisher} from '../content';
import type {Dictionary,Locale} from '../i18n';

export default function Home({locale,dictionary}:{locale:Locale;dictionary:Dictionary}) {
  const t=dictionary.home;
  const data={'@context':'https://schema.org','@type':'WebSite',name:'LifeTalea',url:`${siteUrl}/${locale}/`,inLanguage:locale,description:t.metaDescription,...(publisher?{publisher:{'@type':'Organization',name:publisher}}:{})};
  const chapters=[
    {title:t.personalTitle,body:t.personalBody,label:t.personalLink,slug:'family-memory-journal'},
    {title:t.voiceTitle,body:t.voiceBody,label:t.voiceLink,slug:'voice-story-recording'},
    {title:t.keepsakeTitle,body:t.keepsakeBody,label:t.keepsakeLink,slug:'keepsake-books'}
  ];
  const number=new Intl.NumberFormat(locale,{minimumIntegerDigits:2});
  return <main id="main">
    <script type="application/ld+json" dangerouslySetInnerHTML={{__html:JSON.stringify(data).replace(/</g,'\\u003c')}}/>
    <section className="hero"><div><h1>{t.titleFirst}<br/>{t.titleSecond}</h1><p>{t.subtitle}</p><Link className="button" href={`/${locale}/features/`}>{t.explore}</Link></div><img src="/hero-book.webp" alt={t.imageAlt} width="640" height="427" fetchPriority="high"/></section>
    <section className="chapters" aria-label={t.waysLabel}>{chapters.map((chapter,index)=><article key={chapter.slug}><span className="chapter-number" aria-hidden="true">{number.format(index+1)}</span><div><h2>{chapter.title}</h2><p>{chapter.body}</p><Link href={`/${locale}/${chapter.slug}/`}>{chapter.label} <span className="direction-arrow" aria-hidden="true">→</span></Link></div></article>)}</section>
    <section className="quiet"><h2>{t.privacyTitle}</h2><p>{t.privacyBody}</p><Link href={`/${locale}/privacy/`}>{t.privacyLink}</Link>{listingUrl?<a className="button" href={listingUrl}>{t.storeLink}</a>:<p className="release-note">{t.releaseNote}</p>}</section>
  </main>;
}
