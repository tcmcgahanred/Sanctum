"""
Regression fixtures for the 2026-08-24 scoring work.

TWO ORIGINS, AND THE DIFFERENCE MATTERS.

  RECONSTRUCTED - written to reproduce the *reason string* a staging document
  reported, because the corpus lives on the collector host. These test the
  RULES faithfully and the articles only approximately.

  OBSERVED - the real headline, taken verbatim from WCTI_20260824. Bodies are
  still summarised, but the title is exactly what was published.

That distinction is not bookkeeping. The first pass of this work used only
reconstructions, and they were more generous than reality: they contained the
phrases the new rules required, so they passed while the real CISA advisory -
which says "Active Threat", not "actively exploited" - fell two tiers. A
fixture written by whoever wrote the rule will tend to confirm the rule.
Observed titles are the correction.
"""

_FILLER = (" The company declined to comment further on the timeline. Analysts said the "
           "disclosure followed standard notification practice, and shares were unchanged "
           "in morning trading. A spokesperson pointed to the firm's published transparency "
           "report and said customers would be contacted individually where required. ")

FALSE_POSITIVES = [
    dict(  # RECONSTRUCTED
        key="australian-hotel",
        title="Australian hotel chain discloses breach affecting 1.2 million guests",
        published="Fri, 22 Aug 2026 09:00:00 GMT",
        url="https://www.theregister.com/a",
        text=("An Australian hospitality group has disclosed a data breach exposing guest "
              "records across its resort portfolio." + _FILLER +
              "The properties include a water park and landscaped grounds." + _FILLER +
              "An extortion demand was received two days later, the company said." + _FILLER +
              "Unrelated industry guidance this month reminded operators to patch Fortinet "
              "edge devices." + _FILLER +
              "Analysts noted a rise in actively exploited flaws across the sector." + _FILLER +
              "Booking software is often supplied by a third-party vendor." + _FILLER +
              "No hospital or government systems were involved."),
    ),
    dict(  # RECONSTRUCTED
        key="aliexpress-fingerprinting",
        title="AliExpress app accused of covert device fingerprinting",
        published="Thu, 21 Aug 2026 12:00:00 GMT",
        url="https://www.theregister.com/b",
        text=("Researchers say the shopping app collects hardware identifiers without "
              "consent." + _FILLER +
              "Regulators are reviewing whether the data could be exfiltrated to brokers." + _FILLER +
              "The report also surveys the wider ecosystem, noting that a water utility in "
              "Europe was studied as a comparison case." + _FILLER +
              "Separately, researchers catalogued zero-day disclosure trends across mobile "
              "SDKs." + _FILLER +
              "Similar telemetry appears in some router and firewall management apps." + _FILLER +
              "An npm package used by the SDK was updated."),
    ),
    dict(  # RECONSTRUCTED
        key="comcast-wifi",
        title="Comcast rolls out new Wi-Fi gateway with built-in protections",
        published="Wed, 20 Aug 2026 15:00:00 GMT",
        url="https://www.theregister.com/c",
        text=("The cable operator says its new router blocks known malicious domains, and "
              "the firewall feature is enabled by default." + _FILLER +
              "Older equipment remained vulnerable to a known exploited flaw for months." + _FILLER +
              "The company also operates a water-cooled data centre in the region, adjacent "
              "to a municipal water district service area." + _FILLER +
              "School district buyers can order the hardware through a procurement portal."),
    ),
    dict(  # RECONSTRUCTED
        key="ice-meta-glasses",
        title="ICE agents spotted wearing Meta smart glasses at enforcement operation",
        published="Wed, 20 Aug 2026 18:00:00 GMT",
        url="https://www.theregister.com/d",
        text=("Civil liberties groups raised privacy concerns after officers were photographed "
              "wearing camera-equipped eyewear. A sheriff's department said it had no role in "
              "the operation. Advocates warned the footage could be compromised or leaked if "
              "the vendor's cloud storage were breached. Meta said the device uses encrypted "
              "transport. Critics compared it to a police department body-camera contract "
              "awarded through an expedited procurement."),
    ),
    dict(  # OBSERVED title
        key="top10-wifi-listicle",
        title="Top 10 Best Wireless / Wi-Fi Security Solutions in 2026",
        published="Tue, 19 Aug 2026 08:00:00 GMT",
        url="https://cybersecuritynews.com/a",
        text=("Choosing the right wireless security platform matters. Our roundup covers "
              "Fortinet, Cisco, SonicWall and Netgear offerings for small networks. Several "
              "have appeared on CISA's known exploited vulnerabilities list, and a zero-day "
              "is always a possibility. We rate each firewall and VPN option. A good router "
              "protects against ransomware delivery and phishing."),
    ),
    dict(  # OBSERVED title
        key="27-biggest-breaches",
        title="27 Biggest Data Breaches in History: Famous Examples",
        published="Mon, 18 Aug 2026 08:00:00 GMT",
        url="https://www.huntress.com/blog/a",
        text=("From Yahoo to Equifax, here are the largest incidents on record. Each data "
              "breach exposed millions of records. Some involved ransomware and extortion; "
              "others were a supply chain compromise. Sectors hit include healthcare, "
              "government, a school district, a university, and a water utility. Many were "
              "traced to an unpatched VPN or firewall, and several flaws were actively "
              "exploited before disclosure."),
    ),
    dict(  # REGRESSION GUARD
        key="uc-substring-collision",
        title="Pokemon Center data breach exposes customer information",
        published="Sat, 23 Aug 2026 09:00:00 GMT",
        url="https://www.bleepingcomputer.com/a",
        text=("The company said a product breach exposed customer records. Analysts urged "
              "shoppers to reduce risk by rotating credentials, and noted the structure of "
              "the retailer's loyalty programme made the data attractive."),
        # `geo` carries the padded terms ' calif ', 'uc ' and 'csu '. A proximity
        # atom that strips that padding matches a bare 'uc' by substring, with no
        # word boundary, inside "product", "reduce" and "structure" - which fired
        # force-surface rule M1 on 190 articles with no California content at all.
        # Nothing here is in the AOR. If M1 fires on this, the guard is broken.
    ),
    dict(  # OBSERVED title - secondary mention of a CISA directive
        key="trueconf-secondary",
        title="Homeland security cybercops say patch TrueConf (Russia's Zoom) if you use it",
        published="Fri, 21 Aug 2026 10:00:00 GMT",
        url="https://www.theregister.com/e",
        text=("CISA has told federal agencies to patch TrueConf Server, saying the flaw is "
              "actively exploited in the wild."),
        # The CISA floor must NOT apply here. This is a trade write-up about a
        # directive, not the directive. Work order 2026-08-24, decision 5:
        # "the signal must come from the authoritative CISA feed itself".
    ),
]

TRUE_POSITIVES = [
    dict(  # OBSERVED title - the case the first pass got wrong
        key="cisa-siemens-s7",
        title="Defending Against an Active Threat to Siemens S7 Series PLCs",
        published="Fri, 22 Aug 2026 16:00:00 GMT",
        url="https://www.cisa.gov/news-events/alerts/aa26-231a",
        text=("CISA is aware of an active threat to Siemens S7 series programmable logic "
              "controller devices used at water and wastewater systems. Asset owners should "
              "review internet exposure and apply mitigations."),
        # The reconstructed version said "actively exploited" and carried a CVE,
        # so it passed at 9.0 while the real advisory fell to 1.5. The published
        # wording is "Active Threat". That is why observed titles exist.
    ),
    dict(  # OBSERVED title
        key="lausd-school-district",
        title="Hackers Release Stolen Data From State's Largest School District",
        published="Thu, 21 Aug 2026 14:00:00 GMT",
        url="https://www.californiacitynews.org/b",
        text=("The group published files taken from the district earlier this year, "
              "including staff records."),
        # Needs `hackers` and `stolen data` in the incident vocabulary. Without
        # them, `school district` matched in the title and the rule still failed
        # for want of an incident word. Word order and plurality are not details.
    ),
    dict(  # RECONSTRUCTED
        key="medusa-ransomware-cisa",
        title="CISA warns of Medusa ransomware targeting school districts and local government",
        published="Thu, 21 Aug 2026 14:00:00 GMT",
        url="https://www.cisa.gov/news-events/alerts/medusa",
        text=("A joint advisory describes Medusa ransomware operators gaining initial access "
              "through exposed RDP and unpatched VPN appliances, then deploying encryption "
              "across municipal networks. Victims include a school district and a county "
              "government. The group runs a leak site and practises double extortion. "
              "CVE-2026-2288 is among the flaws actively exploited in these intrusions."),
    ),
    dict(  # RECONSTRUCTED
        key="fortinet-kev-advisory",
        title="Fortinet FortiGate flaw added to CISA KEV catalog after in-the-wild exploitation",
        published="Wed, 20 Aug 2026 11:00:00 GMT",
        url="https://www.bleepingcomputer.com/b",
        text=("CISA added CVE-2026-3310, a path traversal flaw in Fortinet FortiGate VPN "
              "appliances, to its known exploited vulnerabilities catalog after confirming "
              "exploitation in the wild. Small local government networks running the "
              "affected firewall builds are considered at elevated risk."),
    ),
    dict(  # RECONSTRUCTED
        key="ca-water-district-ransomware",
        title="Sacramento County water district hit by ransomware, systems offline",
        published="Fri, 22 Aug 2026 20:00:00 GMT",
        url="https://news.google.com/x",
        text=("A water district serving parts of Sacramento County confirmed a ransomware "
              "attack that took billing systems offline. The utility said drinking water "
              "operations were unaffected. Cal OES is assisting."),
    ),
]

# Items that must land AT OR ABOVE their floor and must NOT be force-surfaced.
# Visible for review, never guaranteed a place.
FLOORED = [
    dict(
        key="trueconf-cisa-directive",
        title="CISA orders agencies to patch actively exploited TrueConf Server flaws",
        published="Fri, 21 Aug 2026 09:00:00 GMT",
        url="https://www.cisa.gov/news-events/alerts/trueconf",
        text=("TrueConf Server contains vulnerabilities that are being exploited. Federal "
              "agencies must apply the update within three weeks."),
        # TrueConf is not on the low-maturity technology list, so tier 3 and M2
        # correctly decline it. The floor makes it visible without letting a
        # niche-product directive climb the surface. Work order decision 5.
        min_score=2.0,
    ),
]

ALL = FALSE_POSITIVES + TRUE_POSITIVES + FLOORED
