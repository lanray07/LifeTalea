import Home from '../../components/Home';
import { notFound } from 'next/navigation';
export function generateStaticParams(){return [{locale:'en-GB'}]}
export const dynamicParams=false;
export const metadata = {alternates:{canonical:'/en-GB/',languages:{'en-GB':'/en-GB/','x-default':'/en-GB/'}}};
export default async function Page({params}:{params:Promise<{locale:string}>}){if((await params).locale!=='en-GB')notFound();return <Home/>}
