'use client';
import {usePathname} from 'next/navigation';
type Props={locale:string;options:{tag:string;label:string}[];label:string;deviceLabel:string};
export default function LocaleSwitcher({locale,options,label,deviceLabel}:Props) {
  const pathname=usePathname();
  function change(next:string) {
    if(!options.some(option=>option.tag===next))return;
    try{localStorage.setItem('lifetalea.locale',next);}catch{/* Language still changes if storage is blocked. */}
    const segments=pathname.split('/').filter(Boolean);segments[0]=next;
    window.location.assign(`/${segments.join('/')}/`);
  }
  return <div className="language-control"><label>{label}<select value={locale} onChange={event=>change(event.target.value)}>{options.map(option=><option key={option.tag} value={option.tag} lang={option.tag}>{option.label}</option>)}</select></label><button type="button" onClick={()=>{try{localStorage.removeItem('lifetalea.locale');}catch{}window.location.assign('/');}}>{deviceLabel}</button></div>;
}
