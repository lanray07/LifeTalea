import type { Metadata } from 'next';
import Link from 'next/link';
import {notFound} from 'next/navigation';
import {siteUrl} from '../../../content';
import {locales,hasLocale,getDictionary,direction,languageNames,preview,socialMetadata} from '../../../i18n';
import LocaleSwitcher from '../../../components/LocaleSwitcher';
import '../../style.css';
type Props={children:React.ReactNode;params:Promise<{locale:string}>};
export const dynamicParams=false;
export function generateStaticParams(){return locales.map(locale=>({locale}));}
export async function generateMetadata({params}:Props):Promise<Metadata>{
  const {locale}=await params;if(!hasLocale(locale))return {};
  const d=getDictionary(locale);
  return {metadataBase:new URL(siteUrl),title:{default:d.home.metaTitle,template:'%s | LifeTalea'},description:d.home.metaDescription,icons:{icon:'/logo.svg'},robots:preview?{index:false,follow:false}:{index:true,follow:true},openGraph:socialMetadata(locale,d.home.metaTitle,d.home.metaDescription,d.home.imageAlt)};
}
export default async function Layout({children,params}:Props) {
  const {locale}=await params;if(!hasLocale(locale))notFound();const {ui}=getDictionary(locale);
  return <html lang={locale} dir={direction(locale)}><body><a href="#main" className="skip">{ui.skip}</a><header><Link href={`/${locale}/`} className="brand"><img src="/logo.svg" width="44" height="44" alt=""/>LifeTalea</Link><nav aria-label={ui.mainNavigation}><Link href={`/${locale}/features/`}>{ui.features}</Link><Link href={`/${locale}/privacy/`}>{ui.privacy}</Link><Link href={`/${locale}/support/`}>{ui.support}</Link></nav><LocaleSwitcher locale={locale} options={languageNames()} label={ui.language} deviceLabel={ui.deviceLanguage}/></header>{preview && <p className="translation-notice">{ui.previewNotice}</p>}{children}<footer><p>{ui.footerNote}</p><div><Link href={`/${locale}/languages/`}>{ui.languages}</Link><Link href={`/${locale}/pricing/`}>{ui.pricing}</Link><Link href={`/${locale}/faq/`}>{ui.faq}</Link><Link href={`/${locale}/contact/`}>{ui.contact}</Link></div><small>© {new Intl.NumberFormat(locale,{useGrouping:false}).format(new Date().getFullYear())} LifeTalea · {ui.brandNotice}</small></footer></body></html>;
}
