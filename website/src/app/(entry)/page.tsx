import AutoLocale from '../../components/AutoLocale';
import {locales,languageNames} from '../../i18n';
export const metadata={title:'LifeTalea — Choose your language',alternates:{canonical:'/en-GB/'}};
export default function Page(){return <><AutoLocale locales={[...locales]}/><main id="main" className="article"><h1>LifeTalea</h1><p>Choose your language</p><div className="related">{languageNames().map(option=><a key={option.tag} href={`/${option.tag}/`} lang={option.tag}>{option.label}</a>)}</div></main></>;}
