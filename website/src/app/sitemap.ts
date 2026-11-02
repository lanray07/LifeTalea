import type {MetadataRoute} from 'next';
import {articles,siteUrl} from '../content';
export const dynamic='force-static';
export default function sitemap():MetadataRoute.Sitemap{return ['',...Object.keys(articles)].map(slug=>({url:`${siteUrl}/en-GB/${slug?slug+'/':''}`,alternates:{languages:{'en-GB':`${siteUrl}/en-GB/${slug?slug+'/':''}`}}}));}
