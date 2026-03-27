
# DEPLOYMENT CHECKLIST

## Pre-deployment
- [ ] Test locally: bin/handrail doctor
- [ ] Run: git push origin main
- [ ] Verify GitHub repo is public

## Vercel Deployment
- [ ] Go to https://vercel.com/new
- [ ] Import project from GitHub
- [ ] Add environment variables:
  - STRIPE_SECRET_KEY
  - STRIPE_PUBLIC_KEY
- [ ] Deploy

## Stripe Setup
- [ ] Create Stripe account: https://stripe.com
- [ ] Create product "Handrail Pro"
- [ ] Create price: $29/month
- [ ] Copy price ID to environment
- [ ] Enable webhooks

## Launch
- [ ] Test install: curl -s https://YOUR_DOMAIN/install.sh | bash
- [ ] Test execute: handrail doctor
- [ ] Tweet announcement
- [ ] Post to HN
- [ ] Submit to Product Hunt

## Revenue Tracking
- [ ] Setup: Stripe Dashboard → Billing
- [ ] Monitor: Daily active users
- [ ] Target: 100 signups / $3K MRR by day 30
