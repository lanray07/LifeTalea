import type {MetadataRoute} from 'next';
import {siteUrl} from '../content';
export const dynamic='force-static';
export default function robots():MetadataRoute.Robots{return {rules:{userAgent:'*',...(process.env.SITE_URL?{allow:'/'}:{disallow:'/'})},sitemap:`${siteUrl}/sitemap.xml`}}
