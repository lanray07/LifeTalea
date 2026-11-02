import type {MetadataRoute} from 'next';
import {articles,siteUrl} from '../content';
import {locales,alternates} from '../i18n';
export const dynamic='force-static';
export default function sitemap():MetadataRoute.Sitemap{return locales.flatMap(locale=>['',...Object.keys(articles)].map(slug=>({url:`${siteUrl}/${locale}/${slug?slug+'/':''}`,alternates:{languages:Object.fromEntries(Object.entries(alternates(locale,slug).languages).map(([tag,url])=>[tag,`${siteUrl}${url}`]))}})));}
