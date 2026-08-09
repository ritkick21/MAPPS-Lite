# MAPPS-Lite Week 7 Redox Chemistry Analysis

## Objective

This stage evaluates whether each surviving cathode candidate contains chemically plausible transition-metal redox chemistry capable of supporting lithium extraction and reinsertion.

Charge-balanced oxidation states are inferred using pymatgen. The most probable assignment is used as the primary screening hypothesis.

**Important:** oxidation-state plausibility does not prove electrochemical reversibility, operating voltage, kinetic performance, or cycling stability.

## Summary

- Candidates analyzed: **10**
- Charge-balanced oxidation-state solutions: **10/10**
- STRONG: **9**
- MODERATE: **1**

## Redox Screening Ranking

| Rank | Material | Formula | Redox Metals | Electrons | Score | Rating | Confidence |
|---:|---|---|---|---:|---:|---|---|
| 1 | mp-850939 | Li2MnV(P2O7)2 | V, Mn | 2.00 | 93.0 | STRONG | MODERATE |
| 2 | mp-6396 | Li3V2(PO4)3 | V | 3.00 | 91.0 | STRONG | MODERATE |
| 3 | mp-849522 | Li8V3P8O29 | V | 5.00 | 91.0 | STRONG | MODERATE |
| 4 | mp-780606 | Li3Cr2(PO4)3 | Cr | 3.00 | 91.0 | STRONG | MODERATE |
| 5 | mp-775982 | Li3V2P4(HO8)2 | V | 3.00 | 91.0 | STRONG | MODERATE |
| 6 | mp-759232 | LiMnV(P2O7)2 | V, Mn | 1.00 | 89.0 | STRONG | MODERATE |
| 7 | mp-18860 | Li2VSiO5 | V | 1.00 | 87.0 | STRONG | HIGH |
| 8 | mp-26963 | LiVPO5 | V | 1.00 | 87.0 | STRONG | HIGH |
| 9 | mp-25410 | LiMnPO4F | Mn | 1.00 | 87.0 | STRONG | HIGH |
| 10 | mp-1539853 | LiV(OF)2 | V | 0.00 | 58.0 | MODERATE | HIGH |

## Candidate Redox Details

### 1. Li2MnV(P2O7)2 (mp-850939)

- Redox score: **93.0/100**
- Redox rating: **STRONG**
- Evidence confidence: **MODERATE**
- Oxidation inference method: COMMON_STATES
- Plausible oxidation-state combinations: 13
- Primary oxidation-state assignment: Li+1, O-2, P+5, V+4, Mn+2
- Alternative assignments: Li+1, O-2, P+5, V+3, Mn+3 | Li+1, O-2, P+5, V+2, Mn+4 | Li+1, O-2, P+4.75, V+5, Mn+2
- Redox-active metals: V, Mn
- Proposed redox window: V(+4.00 → up to +5); Mn(+2.00 → up to +4)
- Lithium inventory per reduced formula: 2.00
- Raw transition-metal oxidation inventory: 3.00 e⁻/formula
- Conservative Li-limited electron estimate: **2.00 e⁻/formula**

**Positive indicators**

- Framework elements have conventional charge-balanced oxidation states.
- Contains transition-metal species capable of supporting cathode redox chemistry.
- Multiple transition-metal oxidation equivalents are chemically available before the selected upper oxidation-state limits.
- The reduced formula contains multiple lithium ions that could potentially participate in delithiation.
- Starting chemistry overlaps with familiar transition-metal redox windows: Mn2+/Mn3+; V3+/V4+, V4+/V5+.

### 2. Li3V2(PO4)3 (mp-6396)

- Redox score: **91.0/100**
- Redox rating: **STRONG**
- Evidence confidence: **MODERATE**
- Oxidation inference method: COMMON_STATES
- Plausible oxidation-state combinations: 5
- Primary oxidation-state assignment: Li+1, O-2, P+5, V+3
- Alternative assignments: Li+1, O-2, P+4.33333, V+4 | Li+1, O-2, P+4.66667, V+3.5 | Li+1, O-2, P+3.66667, V+5
- Redox-active metals: V
- Proposed redox window: V(+3.00 → up to +5)
- Lithium inventory per reduced formula: 3.00
- Raw transition-metal oxidation inventory: 4.00 e⁻/formula
- Conservative Li-limited electron estimate: **3.00 e⁻/formula**

**Positive indicators**

- Framework elements have conventional charge-balanced oxidation states.
- Contains transition-metal species capable of supporting cathode redox chemistry.
- Multiple transition-metal oxidation equivalents are chemically available before the selected upper oxidation-state limits.
- The reduced formula contains multiple lithium ions that could potentially participate in delithiation.
- Starting chemistry overlaps with familiar transition-metal redox windows: V3+/V4+.

### 3. Li8V3P8O29 (mp-849522)

- Redox score: **91.0/100**
- Redox rating: **STRONG**
- Evidence confidence: **MODERATE**
- Oxidation inference method: COMMON_STATES
- Plausible oxidation-state combinations: 6
- Primary oxidation-state assignment: Li+1, O-2, P+5, V+3.33333
- Alternative assignments: Li+1, O-2, P+4.75, V+4 | Li+1, O-2, P+4.875, V+3.66667 | Li+1, O-2, P+4.625, V+4.33333
- Redox-active metals: V
- Proposed redox window: V(+3.33 → up to +5)
- Lithium inventory per reduced formula: 8.00
- Raw transition-metal oxidation inventory: 5.00 e⁻/formula
- Conservative Li-limited electron estimate: **5.00 e⁻/formula**

**Positive indicators**

- Framework elements have conventional charge-balanced oxidation states.
- Contains transition-metal species capable of supporting cathode redox chemistry.
- Multiple transition-metal oxidation equivalents are chemically available before the selected upper oxidation-state limits.
- The reduced formula contains multiple lithium ions that could potentially participate in delithiation.
- Starting chemistry overlaps with familiar transition-metal redox windows: V3+/V4+.

### 4. Li3Cr2(PO4)3 (mp-780606)

- Redox score: **91.0/100**
- Redox rating: **STRONG**
- Evidence confidence: **MODERATE**
- Oxidation inference method: COMMON_STATES
- Plausible oxidation-state combinations: 7
- Primary oxidation-state assignment: Li+1, O-2, P+5, Cr+3
- Alternative assignments: Li+1, O-2, P+4.66667, Cr+3.5 | Li+1, O-2, P+4.33333, Cr+4 | Li+1, O-2, P+3, Cr+6
- Redox-active metals: Cr
- Proposed redox window: Cr(+3.00 → up to +6)
- Lithium inventory per reduced formula: 3.00
- Raw transition-metal oxidation inventory: 6.00 e⁻/formula
- Conservative Li-limited electron estimate: **3.00 e⁻/formula**

**Positive indicators**

- Framework elements have conventional charge-balanced oxidation states.
- Contains transition-metal species capable of supporting cathode redox chemistry.
- Multiple transition-metal oxidation equivalents are chemically available before the selected upper oxidation-state limits.
- The reduced formula contains multiple lithium ions that could potentially participate in delithiation.
- Starting chemistry overlaps with familiar transition-metal redox windows: Cr3+/Cr4+.

### 5. Li3V2P4(HO8)2 (mp-775982)

- Redox score: **91.0/100**
- Redox rating: **STRONG**
- Evidence confidence: **MODERATE**
- Oxidation inference method: COMMON_STATES
- Plausible oxidation-state combinations: 6
- Primary oxidation-state assignment: H+1, Li+1, O-2, P+5, V+3.5
- Alternative assignments: H0, Li+1, O-2, P+5, V+4.5 | H+1, Li+1, O-2, P+4.75, V+4 | H+1, Li+1, O-2, P+4.5, V+4.5
- Redox-active metals: V
- Proposed redox window: V(+3.50 → up to +5)
- Lithium inventory per reduced formula: 3.00
- Raw transition-metal oxidation inventory: 3.00 e⁻/formula
- Conservative Li-limited electron estimate: **3.00 e⁻/formula**

**Positive indicators**

- Framework elements have conventional charge-balanced oxidation states.
- Contains transition-metal species capable of supporting cathode redox chemistry.
- Multiple transition-metal oxidation equivalents are chemically available before the selected upper oxidation-state limits.
- The reduced formula contains multiple lithium ions that could potentially participate in delithiation.
- Starting chemistry overlaps with familiar transition-metal redox windows: V3+/V4+.

### 6. LiMnV(P2O7)2 (mp-759232)

- Redox score: **89.0/100**
- Redox rating: **STRONG**
- Evidence confidence: **MODERATE**
- Oxidation inference method: COMMON_STATES
- Plausible oxidation-state combinations: 10
- Primary oxidation-state assignment: Li+1, O-2, P+5, V+5, Mn+2
- Alternative assignments: Li+1, O-2, P+5, V+4, Mn+3 | Li+1, O-2, P+5, V+3, Mn+4 | Li+1, O-2, P+4.75, V+5, Mn+3
- Redox-active metals: V, Mn
- Proposed redox window: V(+5.00 → up to +5); Mn(+2.00 → up to +4)
- Lithium inventory per reduced formula: 1.00
- Raw transition-metal oxidation inventory: 2.00 e⁻/formula
- Conservative Li-limited electron estimate: **1.00 e⁻/formula**

**Positive indicators**

- Framework elements have conventional charge-balanced oxidation states.
- Contains transition-metal species capable of supporting cathode redox chemistry.
- At least one electron equivalent of transition-metal oxidation is available.
- Starting chemistry overlaps with familiar transition-metal redox windows: Mn2+/Mn3+; V4+/V5+.

**Redox concerns**

- V begins near the conservative upper oxidation-state limit (+5.00), leaving little conventional cation-redox headroom.

### 7. Li2VSiO5 (mp-18860)

- Redox score: **87.0/100**
- Redox rating: **STRONG**
- Evidence confidence: **HIGH**
- Oxidation inference method: COMMON_STATES
- Plausible oxidation-state combinations: 1
- Primary oxidation-state assignment: Li+1, O-2, Si+4, V+4
- Redox-active metals: V
- Proposed redox window: V(+4.00 → up to +5)
- Lithium inventory per reduced formula: 2.00
- Raw transition-metal oxidation inventory: 1.00 e⁻/formula
- Conservative Li-limited electron estimate: **1.00 e⁻/formula**

**Positive indicators**

- Framework elements have conventional charge-balanced oxidation states.
- Contains transition-metal species capable of supporting cathode redox chemistry.
- At least one electron equivalent of transition-metal oxidation is available.
- The reduced formula contains multiple lithium ions that could potentially participate in delithiation.
- Starting chemistry overlaps with familiar transition-metal redox windows: V3+/V4+, V4+/V5+.

### 8. LiVPO5 (mp-26963)

- Redox score: **87.0/100**
- Redox rating: **STRONG**
- Evidence confidence: **HIGH**
- Oxidation inference method: COMMON_STATES
- Plausible oxidation-state combinations: 2
- Primary oxidation-state assignment: Li+1, O-2, P+5, V+4
- Alternative assignments: Li+1, O-2, P+4, V+5
- Redox-active metals: V
- Proposed redox window: V(+4.00 → up to +5)
- Lithium inventory per reduced formula: 1.00
- Raw transition-metal oxidation inventory: 1.00 e⁻/formula
- Conservative Li-limited electron estimate: **1.00 e⁻/formula**

**Positive indicators**

- Framework elements have conventional charge-balanced oxidation states.
- Contains transition-metal species capable of supporting cathode redox chemistry.
- At least one electron equivalent of transition-metal oxidation is available.
- Starting chemistry overlaps with familiar transition-metal redox windows: V3+/V4+, V4+/V5+.

### 9. LiMnPO4F (mp-25410)

- Redox score: **87.0/100**
- Redox rating: **STRONG**
- Evidence confidence: **HIGH**
- Oxidation inference method: COMMON_STATES
- Plausible oxidation-state combinations: 2
- Primary oxidation-state assignment: Li+1, O-2, F-1, P+5, Mn+3
- Alternative assignments: Li+1, O-2, F-1, P+4, Mn+4
- Redox-active metals: Mn
- Proposed redox window: Mn(+3.00 → up to +4)
- Lithium inventory per reduced formula: 1.00
- Raw transition-metal oxidation inventory: 1.00 e⁻/formula
- Conservative Li-limited electron estimate: **1.00 e⁻/formula**

**Positive indicators**

- Framework elements have conventional charge-balanced oxidation states.
- Contains transition-metal species capable of supporting cathode redox chemistry.
- At least one electron equivalent of transition-metal oxidation is available.
- Starting chemistry overlaps with familiar transition-metal redox windows: Mn2+/Mn3+, Mn3+/Mn4+.

### 10. LiV(OF)2 (mp-1539853)

- Redox score: **58.0/100**
- Redox rating: **MODERATE**
- Evidence confidence: **HIGH**
- Oxidation inference method: COMMON_STATES
- Plausible oxidation-state combinations: 1
- Primary oxidation-state assignment: Li+1, O-2, F-1, V+5
- Redox-active metals: V
- Proposed redox window: V(+5.00 → up to +5)
- Lithium inventory per reduced formula: 1.00
- Raw transition-metal oxidation inventory: 0.00 e⁻/formula
- Conservative Li-limited electron estimate: **0.00 e⁻/formula**

**Positive indicators**

- Framework elements have conventional charge-balanced oxidation states.
- Contains transition-metal species capable of supporting cathode redox chemistry.
- Starting chemistry overlaps with familiar transition-metal redox windows: V4+/V5+.

**Redox concerns**

- No conventional transition-metal oxidation capacity was identified from the inferred starting oxidation state.
- V begins near the conservative upper oxidation-state limit (+5.00), leaving little conventional cation-redox headroom.

## Scientific Interpretation

Cathode operation normally requires oxidation of a redox-active species during lithium extraction and reduction during lithium reinsertion.

This analysis estimates how much conventional transition-metal oxidation capacity exists between the inferred starting state and a conservative upper oxidation state for each metal.

The estimate is then limited by the amount of lithium available in the reduced chemical formula. This prevents the screening model from assigning more conventional Li-coupled electrons than the composition contains.

A high redox score therefore means that the composition has a plausible charge-balanced starting chemistry, one or more recognizable transition-metal redox centers, and meaningful conventional oxidation headroom.

It does **not** mean that all predicted electrons can be reversibly extracted in a real battery.

## Next Stage

The next Week 7 stage will combine composition, molar mass, and the conservative electron-transfer estimate to calculate screening-level theoretical specific capacity and related performance descriptors.
