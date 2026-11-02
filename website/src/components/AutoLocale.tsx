'use client';
import {useEffect} from 'react';
import {matchLocale} from '../locale-match';
export default function AutoLocale({locales}:{locales:string[]}) {
  useEffect(()=>{
    let saved:string|null=null;try{saved=localStorage.getItem('lifetalea.locale');}catch{}
    const locale=saved && locales.includes(saved)?saved:matchLocale(navigator.languages,locales);
    window.location.replace(`/${locale}/`);
  },[locales]);
  return null;
}
