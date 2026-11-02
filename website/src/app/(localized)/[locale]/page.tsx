import Home from '../../../components/Home';
import { notFound } from 'next/navigation';
import {hasLocale,getDictionary,alternates} from '../../../i18n';
export const dynamicParams=false;
type Props={params:Promise<{locale:string}>};
export async function generateMetadata({params}:Props){const {locale}=await params;return hasLocale(locale)?{alternates:alternates(locale)}:{};}
export default async function Page({params}:Props){const {locale}=await params;if(!hasLocale(locale))notFound();return <Home locale={locale} dictionary={getDictionary(locale)}/>;}
