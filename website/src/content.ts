import source from './dictionaries/en-GB.json';
export type Article = {title:string;summary:string;sections:{title:string;body:string}[]};
export const siteUrl=(process.env.SITE_URL || 'http://localhost:3000').replace(/\/$/,'');
export const supportEmail=process.env.SUPPORT_EMAIL || 'banksmi@mail.com';
export const publisher=process.env.PUBLISHER_NAME || 'O.Bankole';
export const listingUrl=process.env.AMAZON_LISTING_URL || '';
export const articles:Record<string,Article>=source.articles;
