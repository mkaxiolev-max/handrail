
# GITHUB SETUP

1. Create repo: https://github.com/new
   - Name: handrail
   - Description: Safe execution + deterministic replay for AI-generated code
   - Public
   - Add MIT license

2. Clone locally:
   git clone https://github.com/YOURNAME/handrail.git
   cd handrail
   
3. Add remote:
   git remote add origin https://github.com/YOURNAME/handrail.git
   git branch -M main
   git push -u origin main

4. Protect main branch:
   Settings → Branches → Add rule
   Require pull request reviews: OFF
   Require status checks: OFF
