# Vox — Sanctum Auspicium CTI Staging Draft
**Edition v20260813 (distribution date: Thursday, Aug 13, 2026)**
**Produced (staging): 2026-08-10 · Information current as of (ICOD): 2026-08-10**

*Staging artifact: collected OSINT with light analysis and IR-based prioritization. Not for distribution in this form. Cadence: staging doc ready Monday → individual review/amend Mon–Tue → team review Wednesday → finished report sent Thursday. Items ordered within each section by intelligence-requirement priority.*

> **RECENCY FILTER APPLIED:** Items are filtered on PUBLICATION date, not collection date. Only items published within the collection window (on/after ~Aug 3, 2026) are included. Older items surfaced by the feeds — including a June "FortiBleed" advisory and multi-year-old Google News backfill — were excluded as out-of-window. An older item appears only if it represents an ongoing, still-active incident, and is flagged as such.

> **SOURCE-ACCESS CHECK (before publishing):** Confirm every cited URL is reachable. On 403/paywall, substitute an alternative citation for the same reporting.

> **VERIFICATION FLAGS:** The lead item (Suisun City) is corroborated across multiple news outlets on its core facts (state of emergency, 911 disruption, cyberattack), but scope, attribution, and whether ransomware was involved are NOT confirmed — verify before the finished product. Technical items are largely drawn from one aggregator's weekly roundup; verify each against the primary CISA/vendor advisory (noted per item) before publishing.

---

## NEWS

**20260813-A — California city declares state of emergency after cyberattack disrupts 911 dispatch.** Suisun City, a small municipality in Solano County, declared a local state of emergency on August 8–9, 2026 after a cyberattack disrupted city computer systems, including 911 emergency dispatch and other public-safety services. Reporting describes a cyberattack; it does not confirm ransomware, the responsible party, or the full scope. *Why an SLTT organization should care: a small California local government lost emergency-services systems to a cyber incident — the same profile as many organizations in our region. Suisun City sits in Solano County, just outside the CCIC 34-county area of responsibility, so this is a near-region cautionary parallel rather than an in-AOR incident; the lesson applies directly to our audience.*
*Source: Los Angeles Times, "California city declares a 'state of emergency' after cyberattack on computer systems," Aug 9, 2026.*
*Source: KQED, "Suisun City Declares State of Emergency After Cyberattack," Aug 9, 2026.*
*Source: NBC Bay Area, "Suisun City Council declares state of emergency after cyberattack," Aug 9, 2026.*

**20260813-B — Business-intelligence platform Metabase hit by actively exploited zero-day (CVSS 10.0).** Metabase, a widely used open-source business-intelligence and data-visualization platform, confirmed a critical zero-day (GHSA-vwf4-m7j8-wcjf) actively exploited in the wild. The flaw is an unauthenticated SQL-injection weakness in a publicly reachable password-reset endpoint that lets an attacker gain full administrator control and extract credentials for every database connected to the platform. Metabase's own cloud service was breached August 3 and patched within hours; self-hosted installations remain exposed until updated, and at least two companies have reported customer-data theft. *Why an SLTT organization should care: agencies that self-host analytics or dashboard tools may run this software; because it holds credentials to other databases, one compromise can cascade. Confirm whether any internal or vendor system uses Metabase and that it has been updated.*
*Source: Cyber Security News, "Metabase 0-Day Vulnerability Exploited in the Wild to Gain Admin Access," Aug 9, 2026. Verify against the Metabase security advisory before publishing.*

---

## CTA TTPs

**20260813-C — Remote-management platform flaw exploited to seize downstream customer systems.** An authentication-bypass vulnerability (CVE-2026-18577) in N-able's N-central remote monitoring and management (RMM) platform is being actively exploited to gain full administrative control. Because managed service providers use this platform to administer many downstream customers, a single compromised server can become a supply-chain-scale incident; researchers observed attackers abusing the built-in remote "Take Control" feature for persistence. *Why an SLTT organization should care: many small agencies outsource IT to providers who use platforms like this; compromising the provider compromises every customer. Ask your IT provider whether they use N-central, whether it is patched, and whether it is blocked from the public internet.*
*Source: Cyber Security News, "Weekly Cyber Security Newsletter," Aug 9, 2026. Verify against the CISA KEV entry and N-able advisory before publishing.*

**20260813-D — Attackers abuse Windows Update infrastructure to deliver malware.** Researchers demonstrated an attack chain that hijacks internet-facing Windows Server Update Services (WSUS) to deliver forged, legitimate-looking Windows update packages that domain-joined computers trust and run automatically; a logic flaw lets certain unsigned files bypass signature checks and execute persistently. *Why an SLTT organization should care: update infrastructure is trusted by every endpoint, so its abuse spreads widely and quietly. Agencies running their own WSUS should ensure it is not internet-exposed and apply the recommended authentication protections.*
*Source: Cyber Security News, "Weekly Cyber Security Newsletter," Aug 9, 2026.*

**20260813-E — "CSS bomb" emails turn webmail into real-time password stealers.** Researchers detailed a technique using ordinary email-styling code (CSS) — no JavaScript, no attachment — to hijack webmail interfaces and capture passwords as users type, working against major webmail providers and slipping past antivirus and spam filters. Several providers have issued fixes. *Why an SLTT organization should care: staff using browser-based email are the target, and traditional filters miss this. The practical defense is user awareness (treat unexpected in-email login prompts with suspicion) and blocking auto-loaded remote images.*
*Source: Cyber Security News, "CSS Bomb Attacks Turn Malicious Emails Into Password-Stealing Keyloggers," Aug 9, 2026.*

---

## LATEST ATTACKS OR RISKS

**20260813-F — Remote-access appliance chain exploited for zero-click root; ransomware group attributed.** Attackers chained two vulnerabilities (CVE-2026-15409 and CVE-2026-15410) to gain zero-click root access on SonicWall SMA 1000-series remote-access appliances, with the activity attributed to a ransomware group. Exploitation reportedly began before patches were available; the vendor urges upgrading firmware, states there is no workaround, and advises assuming compromise and rotating credentials. *Why an SLTT organization should care: remote-access appliances sit at the network edge and are common in small agencies; zero-click root means no user action is required. Confirm whether any SonicWall SMA appliances are in use and that firmware is current.*
*Source: Cyber Security News, "Weekly Cyber Security Newsletter," Aug 9, 2026. Verify against the SonicWall advisory before publishing.*

**20260813-G — CISA-flagged Apache Tomcat encryption flaw past its remediation deadline.** CISA added a missing-encryption flaw in Apache Tomcat (CVE-2026-34486) to its Known Exploited Vulnerabilities catalog with a federal remediation deadline of August 7, 2026; researchers observed exploitation deploying reverse shells, and fixed versions are available. *Why an SLTT organization should care: Tomcat underlies many web applications agencies run or buy; the passed KEV deadline signals urgency. Confirm whether any web applications rely on Tomcat and that they are updated — and ask vendors the same.*
*Source: Cyber Security News, "Weekly Cyber Security Newsletter," Aug 9, 2026. Verify against the CISA KEV catalog entry before publishing.*

---

## KEYWORDS

Local government, emergency services, business intelligence, remote monitoring and management, supply chain, Windows update infrastructure, webmail, phishing, remote-access appliance, ransomware, vulnerability exploitation, KEV, credential theft

---

*Collection note: Drawn from national trusted-source feeds and statewide California Google News queries, filtered to items published within the collection window. AOR-direct coverage via curated regional/official sources (MS-ISAC, Cal OES, CA regional press) and the CA AG breach registry is pending build. The Suisun City incident surfaced through the statewide California query; it is near-AOR (Solano County), included as a high-relevance parallel with its boundary status flagged.*
