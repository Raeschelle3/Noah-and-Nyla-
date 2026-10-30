# Website Migration: off ChatGPT, matching Stan

**Owner:** Theo (Senior Technical Expert)

## The problem
The book covers, titles and prices on the website don't match the Stan store. A buyer who sees one cover on TikTok, another on the site and a third on Stan loses trust, and doesn't buy.

## Rule from now on
**Stan is the single source of truth** for covers, titles, prices and descriptions. The website links straight to each Stan product, with no copied prices that can drift out of date.

## Steps
1. **Inventory (needs Rae's links):** list every product on Stan and every product on the website, side by side. Flag mismatched covers, titles, prices and dead links.
2. **Pick the final cover and title** for each book (Rae decides once).
3. **Rebuild the site in this repo**, so Rae owns the code and it isn't locked inside a ChatGPT project.
   - Pages: Home · Books (by collection) · Free Guides · About Rae · Contact.
   - Noah & Nyla gets its own site/page and is not mixed into Rae's books site.
   - Every page reaches a free guide in one tap; phone-first.
4. **Host it free** (GitHub Pages or Netlify) and point Rae's domain at it.
5. **Check before switching:** every link works, every cover matches Stan, email signup delivers the guide, and it looks right on a phone.
6. **Switch the domain**, keep the old site up for 7 days as a backup, then **deactivate the ChatGPT-built site** and cancel anything it's billing for.

## What Theo needs from Rae
- Website URL, and where it's hosted (Wix? Squarespace? a ChatGPT/GPT link? custom domain?)
- Stan store URL
- Domain registrar login (Rae logs in herself; Theo gives step-by-step instructions)
- Final cover files (or permission to pull them from Stan)
