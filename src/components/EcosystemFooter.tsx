'use client';

/**
 * Cod3BlackAgency Ecosystem Footer
 * Shared cross-promotion footer for SEO interlinking between products
 */

type EcosystemProduct = {
  id: string;
  name: string;
  tagline: string;
  url: string;
};

const PRODUCTS: EcosystemProduct[] = [
  {
    id: 'gratog',
    name: 'Taste of Gratitude',
    tagline: 'Wildcrafted Sea Moss & Wellness',
    url: 'https://gratog.vercel.app',
  },
  {
    id: 'sd-studio',
    name: 'SD Studio',
    tagline: 'Stable Diffusion Control Center',
    url: 'https://sd-studio-web.vercel.app',
  },
  {
    id: 'image-to-svg',
    name: 'Image to SVG',
    tagline: 'Convert Images to Vector Graphics',
    url: 'https://image-to-svg-eight.vercel.app',
  },
  {
    id: 'tog-compare',
    name: 'TOG Compare',
    tagline: 'Product Comparison Tool',
    url: 'https://tog-app.vercel.app',
  },
  {
    id: 'eco-pack',
    name: 'Instant Launch Pages',
    tagline: 'DTC Landing Page Templates',
    url: 'https://eco-pack-template.vercel.app',
  },
  {
    id: 'tradealert',
    name: 'TradeAlert',
    tagline: 'Real-Time Trading Signals',
    url: 'https://ktradealerts.vercel.app',
  },
];

function buildUtmUrl(targetUrl: string, source?: string): string {
  try {
    const url = new URL(targetUrl);
    url.searchParams.set('utm_source', source || 'cod3blackagency');
    url.searchParams.set('utm_medium', 'ecosystem-footer');
    url.searchParams.set('utm_campaign', 'cross-promo');
    return url.toString();
  } catch {
    return targetUrl;
  }
}

interface EcosystemFooterProps {
  currentProduct?: string;
  className?: string;
}

export function EcosystemFooter({ currentProduct = 'sd-studio', className = '' }: EcosystemFooterProps) {
  const year = new Date().getFullYear();

  const schema = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'Cod3BlackAgency',
    url: 'https://github.com/wizelements',
    brand: 'Cod3BlackAgency',
    sameAs: ['https://github.com/wizelements'],
    hasPart: PRODUCTS.map((p) => ({
      '@type': 'WebSite',
      name: p.name,
      url: p.url,
    })),
  };

  return (
    <footer className={`border-t border-slate-700 bg-slate-900 ${className}`}>
      <div className="mx-auto max-w-6xl px-4 py-8">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
          {/* Brand Block */}
          <div className="sm:w-1/3">
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">
              By Cod3BlackAgency
            </p>
            <p className="mt-2 text-sm text-slate-400">
              Tools, templates, and apps for builders and creators.
            </p>
          </div>

          {/* Product Links */}
          <nav aria-label="Cod3BlackAgency product ecosystem" className="flex-1">
            <ul className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-2 lg:grid-cols-3">
              {PRODUCTS.map((product) => {
                const isCurrent = product.id === currentProduct;

                if (isCurrent) {
                  return (
                    <li key={product.id}>
                      <span
                        aria-current="page"
                        className="block rounded-lg bg-emerald-900/30 border border-emerald-700/50 px-3 py-2"
                      >
                        <span className="font-medium text-emerald-400">
                          {product.name}
                        </span>
                        <span className="mt-0.5 block text-xs text-emerald-500/70">
                          You&apos;re here
                        </span>
                      </span>
                    </li>
                  );
                }

                return (
                  <li key={product.id}>
                    <a
                      href={buildUtmUrl(product.url, currentProduct)}
                      className="block rounded-lg bg-slate-800 px-3 py-2 transition-colors hover:bg-slate-700 border border-slate-700 hover:border-slate-600"
                    >
                      <span className="font-medium text-slate-200">
                        {product.name}
                      </span>
                      <span className="mt-0.5 block text-xs text-slate-400">
                        {product.tagline}
                      </span>
                    </a>
                  </li>
                );
              })}
            </ul>
          </nav>
        </div>
      </div>

      {/* Copyright */}
      <div className="border-t border-slate-800 px-4 py-4 text-center text-xs text-slate-500">
        © {year} Cod3BlackAgency. All rights reserved.
      </div>

      {/* SEO Schema */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
      />
    </footer>
  );
}

export default EcosystemFooter;
