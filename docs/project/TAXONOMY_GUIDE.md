# Portfolio Performance Taxonomy Guide

This document defines the goals, structures, and constraints for using **custom taxonomies** in [Portfolio Performance (PP)](https://www.portfolio-performance.info/en/).  
It serves as the foundation for classification, rebalancing, and benchmarking against reference models.

---

## 🎯 Goals

1. **Standardized Framework**  
   Align all holdings under a consistent classification structure, anchored to the **BlackRock Target Allocation models** while extended with additional sleeves for Alternatives.

2. **Look-Through Analysis**  
   Support *look-through* reporting for ETFs and mutual funds (via [pp-portfolio-classifier](https://github.com/fizban99/pp-portfolio-classifier)) so sector, region, and factor exposure is visible.

3. **Comparative Benchmarks**  
   Enable side-by-side analysis against three reference portfolios:
   - **70/30 Baseline Portfolio**
   - **BlackRock Target Allocation Multi-Manager with Alts**
   - **BRX-Plus (Custom Public/Private 70/30 split)**

4. **Drift Monitoring**  
   Use PP’s **Rebalancing View** to measure allocation drift versus targets, preserving clear signals (e.g. buffer ETFs and crypto carved out separately).

5. **Multi-Entity Rollups**  
   Maintain flexibility for household-level rollups across LLCs, IRAs, and taxable accounts without embedding entity logic inside the taxonomy.

---

## 🏗️ Taxonomy Structure

### Level 0 (Asset Class)
- **Equity**
- **Fixed Income**
- **Alternatives**
- **Cash & Cash Equivalents**

### Level 1 (Sleeves)
**Equity**
- US Core Beta  
- US Factors & Styles  
- US Growth / Value / Size tilts  
- International Developed  
- Emerging Markets  
- Sector / Thematic (optional)

**Fixed Income**
- Core Aggregate  
- Treasuries (short / intermediate / long)  
- TIPS  
- Investment Grade Credit  
- High Yield  
- Municipals  
- International / Emerging Debt  

**Alternatives**
- Real Estate (Public REITs / Private)  
- Commodities (Gold / Broad)  
- Market Neutral / Hedge Fund-Like  
- Systematic / Multi-Strategy  
- Defined-Outcome / Buffer ETFs  
- Private Markets (Equity / Credit)  
- Crypto (BTC / ETH / Diversified)  

**Cash & Cash Equivalents**
- Money Market / Bank Deposits  
- T-Bills  
- Short-Term Cash Proxies  

### Level 2 (Optional Granularity)
- Equity → Region, Cap Size, Style, Sector  
- Fixed Income → Duration & Credit Bands  
- Alternatives → Strategy / Reference Index / Asset Type  
- Crypto → Layer-1 (BTC/ETH) vs Diversified baskets  
- Cash → Instrument (VMFXX, SGOV, etc.)

---

## 📊 Reference Models

**1. 70/30 Portfolio**
- 70% Equity
- 30% Fixed Income
- 0–2% Cash
- No explicit Alternatives

**2. BlackRock Multi-Manager w/ Alts**
- ~55% Equity
- ~25–30% Fixed Income
- ~15–17% Alternatives (Market Neutral, Systematic, Gold, Bitcoin, Tactical Opportunities)
- ~2% Cash

**3. BRX-Plus (Custom Public/Private 70/30)**
- 70% Public Markets (Equities + Bonds)
- 30% Private/Alternative Markets
  - ~15% Equity-like (PE, VC, Real Estate, Crypto beta)
  - ~15% Bond-like (Private Credit, Absolute Return, Buffer ETFs)

---

## ⚠️ Constraints & Known Issues

- **Cash Treatment**: Kubera JSON exports show cash as ticker `USD`. These must be manually classified into Cash sleeves.  
- **Private Assets**: Real estate, LLCs, and private credit holdings lack tickers. They require **custom security setup** in PP.  
- **Look-Through**: Kubera JSON does not include fund composition data. Must use pp-portfolio-classifier or external data for proper attribution.  
- **Debt & Insurance**: JSON includes liabilities and insurance entries. PP does not natively support these in the taxonomy; track separately if needed.  
- **Manual Classification**: Initial setup requires manual mapping of each security to the taxonomy. Once assigned, the structure persists.  
- **Multiple Benchmarks**: PP does not support multiple target sets simultaneously. Each benchmark must be maintained as a separate **target allocation set**.

---

## 🔧 Implementation Notes

1. **Taxonomy Creation**:  
   `File → New → Taxonomy → Empty Taxonomy` → name it `BRX-Plus` → add nodes per above.

2. **Assign Securities**:  
   - Use **Classifications** tab for each security.  
   - Map listed assets (tickers) directly.  
   - Map private assets manually.  

3. **Rebalancing Targets**:  
   - Enter percentage weights for chosen benchmark.  
   - Save multiple sets (70/30, BlackRock, BRX-Plus) for comparison.  

4. **Entity Separation**:  
   - Keep portfolios (LLCs, IRAs, taxable) separate in PP.  
   - Use filters for reporting instead of mixing them into taxonomy.

---

## 📌 Next Steps

- Generate a **mapping table** (Kubera JSON → Taxonomy Node).  
- Build lightweight ETL (JSON → CSV) to import assets into PP.  
- Validate classifications by reconciling with BlackRock benchmark weights.  
- Document manual overrides for private and alternative holdings.
