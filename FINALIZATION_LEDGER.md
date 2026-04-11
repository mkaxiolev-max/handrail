# NS∞ FINALIZATION LEDGER
Generated: Fri Apr 10 19:01:35 PDT 2026

## Service Status

| Subsystem | Status | Evidence | Blocker | Next Action |
|---|---|---|---|---|
| ns_core | LIVE | healthz ok, voice/chat/intent verified | — | — |
| alexandria | LIVE | healthz ok, receipt chain on NSExternal | — | — |
| model_router | LIVE | 6 providers registered | Groq 401, OpenAI 429, Gemini 429 | Key rotation / billing |
| violet | LIVE | healthz ok, ISR v2 | — | — |
| canon | LIVE | healthz ok | — | — |
| integrity | LIVE | healthz ok | — | — |
| omega | LIVE | healthz ok, advisory_only enforced | — | — |
| Anthropic LLM | LIVE | verified | — | — |
| Grok LLM | LIVE | grok-4.20-reasoning | — | — |
| Ollama LLM | LIVE | llama3:latest local | — | — |
| Gemini LLM | EXTERNAL_BLOCKED | Code correct, quota 429 | Free tier limit | Upgrade or wait |
| OpenAI LLM | EXTERNAL_BLOCKED | Code correct, quota 429 | No credits | platform.openai.com/billing |
| Groq LLM | EXTERNAL_BLOCKED | Code correct, key 401 | Expired key | console.groq.com/keys |
| Voice (inbound) | LIVE | TwiML verified, Pause fix applied | — | — |
| Voice (transcription) | LIVE | python-multipart fix applied, LLM responding | — | — |
| SMS (/voice/sms) | SOFTWARE_COMPLETE | Route verified in code | Twilio console webhook | Set webhook in Twilio |
| frontend :3000 | LIVE | HTTP 200, /violet route live | — | — |
| ns_ui :3002 | LIVE | HTTP 200, orbital view | — | — |
| Handrail | PARALLEL_PRODUCT | Not in compose | Architecture decision needed | See HANDRAIL_ROLE_DECISION.md |
| Stripe | EXTERNAL_BLOCKED | STRIPE_SK_PENDING | LLC verification needed | dashboard.stripe.com |
| YubiKey slot_2 | EXTERNAL_BLOCKED | slot_1 enrolled | Hardware needed | Order YubiKey 5 NFC |
| DNS root.axiolev.com | EXTERNAL_BLOCKED | Not set | GoDaddy CNAME | GoDaddy → Vercel |
