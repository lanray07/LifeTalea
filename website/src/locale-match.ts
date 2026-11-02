export function matchLocale(preferences:readonly string[],available:readonly string[]):string {
  for(const preference of preferences) {
    try {
      const locale=new Intl.Locale(preference);
      const exact=available.find(tag=>tag.toLowerCase()===locale.baseName.toLowerCase());
      if(exact)return exact;
      const language=locale.language;
      if(language==='zh') {
        const script=locale.maximize().script;
        const tag=script==='Hant'?'zh-Hant':'zh-Hans';if(available.includes(tag))return tag;
      }
      if(language==='es' && locale.region && locale.region!=='ES' && available.includes('es-419'))return 'es-419';
      const regional=language==='fr' && locale.region==='CA'?'fr-CA':language==='pt' && locale.region==='PT'?'pt-PT':null;
      if(regional && available.includes(regional))return regional;
      const fallback=available.find(tag=>tag.split('-')[0]===language);if(fallback)return fallback;
    } catch { /* Invalid stored/browser values do not become URL paths. */ }
  }
  return 'en-GB';
}
