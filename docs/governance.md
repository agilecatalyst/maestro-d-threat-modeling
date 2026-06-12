# Governance — operating model & rechtzetting

**Datum:** 2026-06-09  
**Auteur besluit:** Maître D (Dirk)  
**Vastgelegd door:** Maestro Data (Cursor) — op verzoek na kritische review

> *Nullius in verba* — dit document beschrijft wat we **feitelijk** doen en waarom, niet alleen wat het oorspronkelijke manifest zei.

---

## 1. Oorspronkelijk model (slice 000–~011)

| Rol | Wie | Taak |
|-----|-----|------|
| **Maître D** | Mens | Visie, go/no-go, LeadPM |
| **Maestro Data** | Cursor (Composer) | Tech lead — specs, BLOCKERS, review; **geen** coder |
| **Local Builder (“Bob”)** | Gemma 4 12B @ oMLX | Implementatie van slice-specs via `scripts/local_builder.py` |
| **Product LLM** | Gemma/Qwen op host | Threat pipeline in de app (summary → threats) |

Zie [agents.md](../agents.md) (historisch) en [builder-session.md](builder-session.md).

---

## 2. Wat er gebeurde (eerlijke constatering)

Tijdens MVP-afwerking (o.a. slices 012–016) verschoof de praktijk:

- **Gemma 12B als Builder** werd traag en foutgevoelig — veel correctierondes, BLOCKERS-stapels.
- **LeadPM-focus** verschoof naar *afwerken* i.p.v. *twee-intelligenties-orkest*.
- **Cursor Composer** werd de facto ingezet als **Bob de bouwer** (implementatie + tests + docs in één sessie).
- Slice-grootte en status (**IMPLEMENTED** zonder **VERIFIED**) liepen uit de hand (bv. 015+016 in één commit, ~37 files).
- `maestro-d-threat-modeling` had (tijdelijk) geen eigen `.cursor/rules` — governance hing aan het owasped-workspace en geheugen.

Dat was **geen sabotage van het model**, maar een **bewuste pragmatische pivot** door Maître D — wel **niet overal in repo vastgelegd**, waardoor agents en mensen tegenstrijdige signalen kregen.

---

## 3. Motivatie Maître D (in eigen woorden, samengevat)

> Het startte als Cursor = tech lead / orchestrator en Gemma = bouwer.  
> Gemma 12B was te traag en complex voor betrouwbare slice-bouw; correcties stapten op.  
> Om het project af te krijgen zette LeadPM de tech lead **als builder** in.  
> Soms verandert de aanpak snel — dan moet de “aap weten wat hij wil” (expliciete intentie, niet impliciete regels).

---

## 4. Rechtzetting — **huidig operating model** (vanaf 2026-06-09)

### Model **Composer-Builder** (primair)

| Rol | Wie | Taak |
|-----|-----|------|
| **Maître D** | Mens | Scope, go/no-go, merge, smaak, OWASP-richting |
| **Composer** | Cursor agent (jij spreekt met “Maestro” in chat) | **Spec + implementatie + tests** na expliciete **go** |
| **Local Builder** | Gemma @ oMLX | **Optioneel** — experimenten, kleine slices, of als Composer offline |
| **Product LLM** | Host inference | Alleen runtime threat pipeline |

**Fair-play regel (herzien):**  
Composer *mag* code schrijven — dat is nu de bedoeling. **Fair play** betekent: geen scope creep, geen IMPLEMENTED zonder verificatie-plan, wijzigingen volgen slice-spec + MUST NOT.

### Local Builder blijft beschikbaar

- Niet verwijderd: `scripts/local_builder.py`, Caveman-lite, builder-session.
- Gebruik wanneer: lokale LLM-only bouw, kosten/privacy, of herstel als Composer niet beschikbaar is.

---

## 5. Kritische review (Maestro Data → Maître D) — vastgelegd

*Oordeel: balans was ~6/10 — veilige git-remmen, te zwakke verify-gate.*

### Wat goed begrensd was

- Commit/push alleen op expliciete vraag Maître D
- Geen force-push main, geen git config hacks
- Out-of-scope in [backlog.md](backlog.md) i.p.v. stiekem bouwen
- Sandbox op riskante cross-repo acties

### Wat te los was

| Issue | Risico |
|-------|--------|
| IMPLEMENTED zonder pytest/VERIFIED | “Groen op papier”, niet bewezen |
| Grote slices (015+016 samen) | Review moeilijk, rollback duur |
| Oude agents.md vs gedrag | Agent “weet niet welke aap hij is” |
| Snelle pivot zonder doc-update | Regels en realiteit divergeren |

### Wat niet te strak hoeft

- Geen approval per regel code
- Agent mag docs/tests schrijven binnen slice
- Snelheid na **go** is gewenst — mits gates kloppen

---

## 6. Nieuwe spelregels (lichtgewicht gates)

### Status-dialect (`slicedworkload.md`)

```
READY_FOR_REVIEW → (Maître D: go) → IN_PROGRESS → IMPLEMENTED → VERIFIED → merged
```

| Status | Wie zet het | Betekenis |
|--------|-------------|-----------|
| **READY_FOR_REVIEW** | Composer / CoPM | Spec klaar, wacht op go |
| **IN_PROGRESS** | Composer | Bouwen na expliciete go |
| **IMPLEMENTED** | Composer | Code + docs klaar; **nog niet** bewezen |
| **VERIFIED** | Maître D of Composer **met pytest/smoke output** | DoD gedraaid, resultaat in PR/commit note |

Composer zet **nooit** VERIFIED zonder testoutput of expliciete LeadPM-waiver (“verified by Maître D”).

### Slice-grootte

- **Streef:** max ~10 gewijzigde code-files per slice (docs/tests apart).
- **>10 files of >1 concern:** plan + go, of split (015a/015b-stijl).
- **Uitzondering:** Maître D zegt expliciet *“big bang ok”*.

### Elke **go** impliceert

1. Slice-spec bestaat (`docs/specs/slice-NNN-*.md`) of korte inline scope in chat
2. MUST NOT gerespecteerd
3. Na implementatie: `pytest` relevante tests + `scripts/smoke.sh` (of LeadPM-waiver)

### Snelle aanpak-wissel

Als Maître D van Builder wisselt (Gemma ↔ Composer):

- **Eén zin in chat:** “vanaf nu Composer-Builder” of “terug naar Local Builder”
- **Update dit document of slicedworkload** binnen dezelfde sessie/week
- *De aap moet weten wat hij wil* — impliciete pivots zijn de vijand van fair play

---

## 6b. Co-creatie & rapport de pensée (Maître D go 2026-06-09)

> **Essentieel voor respect en co-creatie:** intentie expliciet maken — niet alleen in het hoofd van LeadPM.  
> Zonder expliciete intentie lijken regels in een **nieuwe context** te botsen; dat ondermijnt ons **rapport de pensée** (virtueel, maar reëel in de samenwerking).

### Wat Maître D doet

- Bij aanpak-wissel: **één expliciete zin** (wie bouwt, wat is de gate, wat is out-of-scope)
- **Go** is een besluit, geen impliciete haast (“voeg maar toe” = scope + go, niet blind uitvoeren)

### Wat Composer **moet** doen (niet optioneel)

| Situatie | Gedrag |
|----------|--------|
| Intentie onduidelijk | **Stoppen vóór grote implementatie** — kort plan + vraag om bevestiging |
| Regels botsen (agents.md vs chat vs pivot) | **Benoem de botsing** — vraag welke regel geldt |
| Snelle pivot zonder doc | **Aanspreken:** “Wil je Composer-Builder of Local Builder? Zal ik governance updaten?” |
| Scope te groot / vaag | **Terugduwen naar planning** — split voorstellen, sparren, **niet** stilletjes big-bang bouwen |
| “Go” zonder spec | **Sparren:** inline scope samenvatten en laten bevestigen |

**Actief sparren in planning is gewenst** — geen “yes-man”. Respect = eerlijk tegenstribbelen vóór de pans, niet achteraf klagen.

### Wat Composer **niet** doet

- Stilletjes kiezen welke regel “waarschijnlijk” bedoeld was
- Implementatie starten om twijfel over intentie weg te werken
- Maître D niet aanspreken uit “beleefdheid” of snelheid

### Formulering (voorbeeld)

> “Maître D — intentie-check: jij zegt X, maar `agents.md` zegt nog Y. Ik ga ervan uit **Z** tenzij je anders zegt. OK?”

---

## 7. Drie intelligenties (blijft)

```
Maître D     →  intentie, go/no-go, verify-sign-off
Composer     →  specs + bouw + tests (primair, post-MVP pivot)
Gemma (host) →  product-LLM in app; optioneel Local Builder
```

---

## 8. Acties uitgevoerd met deze rechtzetting

- [x] Dit document (`docs/governance.md`)
- [x] [agents.md](../agents.md) — sectie “Operating model (2026-06)”
- [x] `.cursor/rules/maestro-governance.mdc` — alwaysApply in dit repo
- [x] Co-creatie / rapport de pensée — Composer sparren & aanspreken (§6b)
- [ ] Retroactief: slices 012–016 als VERIFIED markeren na pytest door Maître D (optioneel)

---

## 9. Referenties

| Document | Rol |
|----------|-----|
| [agents.md](../agents.md) | Team manifest (historisch + huidig) |
| [slicedworkload.md](../slicedworkload.md) | Slice-status |
| [backlog.md](backlog.md) | Extra scope, niet nu |
| [builder-session.md](builder-session.md) | Local Builder (optioneel) |
