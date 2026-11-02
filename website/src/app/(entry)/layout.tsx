import {siteUrl} from '../../content';
import '../style.css';
export const metadata={metadataBase:new URL(siteUrl),icons:{icon:'/logo.svg'},robots:{index:false,follow:false}};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en-GB"><body>{children}</body></html>;}
