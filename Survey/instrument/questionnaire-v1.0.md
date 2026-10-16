Handling: Unclassified — working

# Sovereign Supply Chain Survey — questionnaire v1.0.0-pilot

*Generated from the item bank by `Survey/tools/survey.py render`. Do not edit by hand.*

Status: **pilot-draft**. Rotating module topic: **turbopump-supply-chain**.

## Legend

| Code | Segment |
|---|---|
| SUP | Canadian launch-chain suppliers (tier 1-3, incl. materials, AM bureaus, test houses, academic service labs) |
| CON | Consortium members (may also be SUP) |
| PRM | Primes and launch-vehicle developers or integrators |
| GOV | Government buyers and program offices |
| ALY | Allied partners (allied-nation firms and agencies) |

| Code | Feeds |
|---|---|
| M | Milestone evidence for program deliverables |
| T | Control-tower data layer (consented records only) |
| X | Composite benchmark index (aggregate, published) |
| E | Eligibility review for sprint and red-team invitations |

| Code | Format |
|---|---|
| SC | Single choice |
| MC | Multiple choice |
| RK | Ranked choice |
| NUM | Numeric with range validation |
| GRID | Grid of single choices |
| M5 | Five-level anchored maturity scale, always followed by an evidence tier (ET) |
| OT | Short open text, 300 characters, technical-data screen applied |
| CHK | Required checkbox |

**Scored** marks items that also feed private scoring. Weights and rubric thresholds are not published.

**Evidence tier (asked after every M5 item):** ET0 No documentation; ET1 Internal documentation exists; ET2 Documentation available for confidential review; ET3 Externally audited, certified or contractually demonstrated.

**Generic M5 anchors** (used where an item gives none): 1 = Ad hoc. Depends on individuals; no documented process. 2 = Managed. Documented at project level; followed inconsistently. 3 = Defined. Organization-wide standard; routinely followed; owner assigned. 4 = Measured. Quantitative performance data tracked and used for decisions. 5 = Optimizing. Data-driven continuous improvement; extended to suppliers and partners.

## Module A: Screener and consent

Status: core-frozen. Estimated time: 2-3 minutes.

| ID | Question | Format and responses | Segments | Feeds | Scored |
|---|---|---|---|---|---|
| A01 | Which best describes your organization's primary role in the Canadian space-launch supply chain? | SC: Supplier or manufacturer; Service provider (test, engineering, AM bureau); Launch-vehicle developer or integrator; Government buyer or program office; Allied-nation organization; Academic or research; Other *Routing: Assigns primary segment.* | ALL | T, X |  |
| A02 | Select all additional roles your organization holds. | MC: Same list as A01; Consortium member *Routing: Multi-role respondents answer the union of segment items; duplicates suppressed.* | ALL | T |  |
| A03 | Where is your organization headquartered, and where are its space-relevant facilities? | GRID: Country of headquarters; Provinces or territories of facilities | ALL | T, X |  |
| A04 | Is your organization Canadian-controlled? | SC: Canadian-controlled; Foreign-controlled with Canadian operations; Foreign; Prefer not to say | ALL | T, X | Yes |
| A05 | Consent tier. Choose how your responses may be used. | SC: 1 - Aggregate statistics only; 2 - Aggregate plus a confidential organization record in the control-tower data layer; 3 - Tier 2 plus eligibility review for sprint and red-team invitations | ALL | M, T, E |  |
| A06 | I confirm my answers will not include technical data, drawings, specifications or performance data controlled under the Canadian Export Control List, the Controlled Goods Program, US ITAR or any other export-control regime. | CHK *Routing: Gate. Without attestation, threshold items route to categorical-only versions.* | ALL | Gate |  |
| A07 | Is your organization registered in Canada's Controlled Goods Program? | SC: Yes; No; In process; Not applicable | SUP, CON, PRM | T, X |  |

## Module B: Core panel

Status: core-frozen. Estimated time: 8-10 minutes.

| ID | Question | Format and responses | Segments | Feeds | Scored |
|---|---|---|---|---|---|
| B01 | Annual revenue attributable to space and launch activities, last fiscal year. | SC: Under $1M; $1-10M; $10-50M; Over $50M; Prefer not to say | SUP, CON, PRM | T, X | Yes |
| B02 | Full-time-equivalent staff in space or launch work, and the share holding engineering or technical qualifications. | NUM: FTE count; Share band: under 25%, 25-50%, 50-75%, over 75% | SUP, CON, PRM | X | Yes |
| B03 | Which space value-chain categories do you operate in? | MC: Upstream - manufacturing; Upstream - launch; Upstream - ground segment; Upstream - research and engineering services; Downstream - operations; Downstream - applications and services; Other | SUP, CON, PRM, ALY | T, X |  |
| B04 | Which propulsion-related business lines do you serve? | MC: Raw materials; Machining; Additive manufacturing; Fabrication; Seals and interconnects; Test services; Test equipment; Instrumentation; Systems integration; Research and development; Other | SUP, CON, PRM | T, X |  |
| B05 | For your three most critical inputs, how many qualified sources do you have, and where are they? | GRID: Input category; Qualified sources: 1 / 2 / 3+; Source region: Canada / US / other allied / other | SUP, CON, PRM | T, X | Yes |
| B06 | Supply-chain risk management maturity. | M5. 1 = Suppliers known only at tier 1. 2 = Critical-supplier list maintained. 3 = Multi-tier map for critical items, reviewed at least annually. 4 = Risk metrics (lead time, concentration) tracked and acted on. 5 = Risk monitoring shared with customers and suppliers. Plus evidence tier. | SUP, CON, PRM | X, E | Yes |
| B07 | Cyber and supply-chain security maturity for engineering data (Govern, Identify, Protect, Detect, Respond, Recover). | M5 Plus evidence tier. | SUP, CON, PRM | X | Yes |
| B08 | In the past 12 months, has a supply disruption delayed a space or launch deliverable by more than four weeks? If yes, select causes. | MC: No; Materials; Capacity; Export licensing; Quality escape; Test access; Workforce; Financing | SUP, CON, PRM | T, X | Yes |
| B09 | Without new contracts, how long could your space or launch operations continue at current staffing? | SC: Under 6 months; 6-12 months; 12-24 months; Over 24 months; Prefer not to say | SUP, CON | X | Yes |
| B10 | Who owns the IP in your space or launch products? | SC: Wholly owned; Jointly owned; Licensed in; Licensed in with field or territory restrictions; Government-owned background IP; Mixed | SUP, CON, PRM | T, X | Yes |
| B11 | Do any critical inputs or IP licences carry foreign re-transfer or end-use restrictions? | SC: Yes; No; Unsure | SUP, CON, PRM | T, X | Yes |
| B12 | Rate how much each factor constrains Canadian sovereign launch capability. | GRID: Rows: test infrastructure; materials; AM capacity; qualification and traceability evidence; workforce; export controls; procurement predictability; financing; IP access; Scale: not a constraint / minor / moderate / major / severe | ALL | M, X |  |
| B13 | Which sovereign capability gaps would you be willing to help close in the next 12 months? | MC: Materials; Bearings and seals; Additive manufacturing; Traceability and qualification; Test access; Export-control readiness; Workforce; None | SUP, CON, PRM, ALY | E | Yes |
| B14 | What could you contribute to the consortium? | MC: Test time; Materials; Engineering hours; Data; Facilities; Mentoring or training; Capital; None | SUP, CON, PRM, ALY | E | Yes |
| B15 | Which Defence Industrial Strategy sovereign-capability areas is your organization positioned for? | MC: Space launch; Space-based surveillance and reconnaissance; Satellite communications; Space domain awareness; Other | ALL | M, X |  |

## Module C: Rotating module - Turbopump supply chain and IP (wave 1)

Status: rotating. Estimated time: 12-18 minutes.

| ID | Question | Format and responses | Segments | Feeds | Scored |
|---|---|---|---|---|---|
| C01 | How is your organization involved with liquid rocket engine turbopumps or their sub-elements? | MC: Design; Manufacture of whole units; Components (impellers, inducers, turbines, housings, shafts); Bearings; Seals; Materials or powders; Additive manufacturing; Machining or finishing; Cleaning or inspection; Test; Buyer or integrator; Regulator or funder; None *Routing: None routes to the light version (C12, C22, C24, C31 only).* | ALL | T, X |  |
| C02 | Which pump architectures do you work with? | MC: Gas-generator turbopump; Staged combustion; Expander; Electric-motor pump; Pressure-fed (no pump); Unsure | SUP, CON, PRM | T |  |
| C03 | Development stage of your turbopump-related work. | SC: Concept; Component test; Subscale pump test; Full-scale pump test; Engine-integrated hot fire; Flight | SUP, CON, PRM | M, X | Yes |
| C04 | For each input, indicate source region, number of qualified sources and typical lead time: nickel superalloy bar or forgings; nickel or titanium AM powder; copper alloys; hydrogen-resistant alloys; cryogenic bearing steels; ceramic or hybrid bearing elements; dynamic seals. | GRID: Source region: Canada / US / EU-UK / other allied / other; Qualified sources: 0 / 1 / 2 / 3+; Lead time: under 3 / 3-6 / 6-12 / over 12 months | SUP, CON, PRM | T, X | Yes |
| C05 | Is any input in C04 single-sourced from outside Canada with no qualified alternative? Describe mitigation without technical data. | OT: Yes or no per input; Mitigation text | SUP, CON, PRM | M, T, X | Yes |
| C06 | Bearing and seal qualification maturity. | M5. 1 = Commercial parts, no cryogenic qualification. 2 = Vendor data relied on. 3 = In-house qualification test procedure. 4 = Life data tracked across runs. 5 = Qualified alternate sources and validated life prediction. Plus evidence tier. | SUP, CON, PRM | X, E | Yes |
| C07 | Which processes do you use or procure for turbopump-class parts? | MC: Laser powder bed fusion; Directed energy deposition; Electron beam; Conventional casting; Forging; Multi-axis machining; Hot isostatic pressing; None | SUP, CON, PRM | T |  |
| C08 | Where is your additive manufacturing capacity for these parts located? | SC: Own equipment in Canada; Canadian bureau; Foreign bureau - US; Foreign bureau - EU-UK; Foreign bureau - other; None | SUP, CON, PRM | T, X | Yes |
| C09 | Additive manufacturing process-control maturity for rotating or pressure-critical parts. | M5. 1 = Prototype prints, no parameter control. 2 = Documented parameters per part. 3 = Qualified process with powder-lot traceability. 4 = In-process monitoring and statistical acceptance data. 5 = Qualified for flight hardware against a customer-accepted specification. Plus evidence tier. | SUP, CON | X, E | Yes |
| C10 | Largest metal additive build envelope available to you in Canada. | SC: Under 250 mm; 250-400 mm; 400-600 mm; Over 600 mm; None | SUP, CON | T, X |  |
| C11 | Which turbopump-relevant tests can you perform in Canada, in-house or by contracted access? | MC: Component spin or balance; Cold-flow water test; Cryogenic (LN2) flow; LOX-compatible flow; Hot-gas turbine test; Engine-integrated hot fire; None | SUP, CON, PRM, GOV | M, T, X | Yes |
| C12 | For tests you cannot perform in Canada, where do you go and what is the typical wait? | GRID: Test type; Location: US / EU-UK / other; Wait: under 1 / 1-3 / 3-6 / over 6 months | SUP, CON, PRM | M, T, X | Yes |
| C13 | Would you offer test capacity to consortium members under a standard access agreement? | SC: Yes; Maybe; No | SUP, CON | E | Yes |
| C14 | Who holds title to your turbopump-related IP? | SC: Own organization; University; Non-profit; Government; Foreign licensor; Joint; Unsure | SUP, CON, PRM | T, X | Yes |
| C15 | Do government funding conditions restrict how you can license or transfer that IP? | SC: Yes; No; Unsure | SUP, CON | T, X |  |
| C16 | IP management maturity. | M5. 1 = No IP register. 2 = Register of patents and confidential know-how. 3 = Background and foreground IP defined in all contracts. 4 = Licensing strategy with field and territory controls, audited. 5 = Portfolio actively used for sovereign licensing and partnering. Plus evidence tier. | SUP, CON, PRM | X, E | Yes |
| C17 | Would you consider licensing turbopump-related IP to Canadian consortium members on standard terms? | SC: Yes; Yes with conditions; No; Not applicable | SUP, CON | E | Yes |
| C18 | Do any of your pump or turbine products or designs meet or exceed the public MTCR Annex Item 3.A.5 thresholds (shaft speed of 8,000 rpm or more, or discharge pressure of 7 MPa or more)? Do not provide specifications. | SC: Yes; No; Unsure *Routing: Shown only after A06 attestation.* | SUP, CON, PRM | T, X |  |
| C19 | Which export-control regimes apply to your turbopump-related work? | MC: Canadian Export Control List; Controlled Goods Program; US ITAR; US EAR; Other allied regime; None; Unsure | SUP, CON, PRM, ALY | T, X | Yes |
| C20 | In the past 24 months, how much have export-licensing timelines delayed turbopump-related work? | SC: No delay; Under 1 month; 1-3 months; 3-6 months; Over 6 months | SUP, CON, PRM, ALY | M, T, X | Yes |
| C21 | Export-control compliance maturity. | M5. 1 = No classification process. 2 = Items classified on request. 3 = Designated official; documented classification and record-keeping. 4 = Audits and training tracked. 5 = Compliance built into design and supplier onboarding. Plus evidence tier. | SUP, CON, PRM | X, E | Yes |
| C22 | Select the three elements whose loss would most delay a sovereign Canadian turbopump program. | RK: Superalloy supply; Additive manufacturing capacity; Bearings; Seals; Traceability and qualification records; Cleaning and oxygen-compatibility capability; Inducer and impeller design expertise; Rotordynamics expertise; Cryogenic test; Hot-fire test; Workforce; IP access | ALL | M, T, X | Yes |
| C23 | If your most critical foreign supplier became unavailable tomorrow, how long would it take to qualify an alternative? | SC: Under 3 months; 3-6 months; 6-12 months; 12-24 months; Over 24 months; No alternative known | SUP, CON, PRM | T, X | Yes |
| C24 | Which one capability investment would most accelerate Canadian turbopump readiness? | OT | ALL | M, E |  |
| C30 | Manufacturing pedigree and traceability maturity for turbopump-class parts (material lot through build, heat treatment, machining, cleaning, inspection and serialization). | M5. 1 = No lot-level traceability. 2 = Paper travellers per part. 3 = Serialized traceability from material lot to finished part. 4 = Queryable digital records linked to nonconformance data. 5 = Digital thread shared with customers and extended to suppliers. Plus evidence tier. | SUP, CON, PRM | M, X, E | Yes |
| C31 | Rank what most limits domestic turbopump supply today. | RK: Qualification and pedigree evidence; Lead time; Cost; Capacity; Design expertise; Test access | ALL | M, X |  |
| C32 | Where can turbopump parts be cleaned and verified for oxygen service? | SC: In-house in Canada; Contracted in Canada; Foreign provider; Not available; Not applicable | SUP, CON, PRM | T, X | Yes |

## Module D: Segment add-ons

Status: core-frozen. Estimated time: 3-5 minutes.

| ID | Question | Format and responses | Segments | Feeds | Scored |
|---|---|---|---|---|---|
| D01 | Expected turbopump or pump-fed engine demand over the next 36 months, with your confidence. | GRID: Units per year: 0 / 1-5 / 6-20 / over 20; Confidence: low / medium / high | PRM | M, T |  |
| D02 | Do you plan to make, buy or partner for turbopumps? | SC: Make; Buy Canadian; Buy foreign; Partner; Undecided | PRM | M, X | Yes |
| D03 | Which procurement or funding instruments are planned for propulsion supply-chain development? | MC: Innovation challenge or contest; Directed procurement; Contribution program; Crown corporation support; None known | GOV | M |  |
| D04 | What evidence would your organization need to accept a Canadian-sourced turbopump component? | MC: Qualification test report; Flight heritage; Third-party certification; Source inspection; Traceability records; Other | GOV, PRM | M, X |  |
| D05 | Under which arrangements could your organization collaborate on Canadian turbopump development? Export-control caveats apply. | MC: Co-development; Licensed production; Test access; Supply; None | ALY | T, E | Yes |

