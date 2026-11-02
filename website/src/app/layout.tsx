import type { Metadata } from 'next';
import Link from 'next/link';
import { siteUrl } from '../content';
import './style.css';
export const metadata: Metadata = { metadataBase: new URL(siteUrl), title: { default: 'LifeTalea — Family stories & voice memories', template: '%s | LifeTalea' }, description: 'A private place for photographs, voices and family stories. Explore the LifeTalea development preview.', robots: process.env.SITE_URL ? {index:true,follow:true} : {index:false,follow:false}, openGraph: { images: ['/hero-book.webp'] } };
export default function Layout({children}:Readonly<{children:React.ReactNode}>) {
  return <html lang="en-GB"><body><a href="#main" className="skip">Skip to content</a><header><Link href="/en-GB/" className="brand"><img src="/logo.svg" width="44" height="44" alt=""/>LifeTalea</Link><nav aria-label="Main"><Link href="/en-GB/features/">Features</Link><Link href="/en-GB/privacy/">Privacy</Link><Link href="/en-GB/support/">Support</Link></nav></header>{children}<footer><p>In development. No account required.</p><div><Link href="/en-GB/languages/">Languages</Link><Link href="/en-GB/pricing/">Pricing</Link><Link href="/en-GB/faq/">FAQ</Link><Link href="/en-GB/contact/">Contact</Link></div><small>© {new Date().getFullYear()} LifeTalea · Working brand pending clearance</small></footer></body></html>;
}
