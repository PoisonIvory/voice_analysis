# Where in the voice does the cycle live? Following the clues, like a detective

### A plain-language final analysis: locating the menstrual-cycle "driver" in my own voice, and what my hormones and PMDD have to do with it

**Author:** Ivy Hamilton (Decibelle)
**Prepared:** June 2026
**What this is:** the last analysis before I pull the whole story together. It is written to be read by a human, not a journal. Where I use a technical word, I explain it right away.

---

## The one-sentence idea

> A doctor can find an injury not only by what stops working, but by what *keeps* working. I use the same trick on my voice: by seeing **which parts of my voice change across my cycle and which parts stay perfectly still**, I can point to *where* the hormones are acting - and rule out where they are not.

This is the "dog that didn't bark" from Sherlock Holmes: the clue was that the dog *stayed silent*. A silence is only a clue if the dog *could* have barked. A big part of this analysis is proving my measurements *could* have detected a change - and then showing they didn't, in exactly the place the theory says they shouldn't.

---

## A 30-second mental model: the voice is a wind instrument

Think of your voice like a clarinet:

- **The reed** = your **vocal folds** (the little flaps in your throat that buzz). This is the **source** of the sound. How wet, swollen, or stiff the reed is changes the *quality* of the buzz - breathy, clear, harsh.
- **The tube** = your **throat and mouth** (the spaces the buzz travels through). This is the **filter**. Its size and shape turn the buzz into recognizable vowels ("ee" vs "ah"). Scientists measure the tube's shape with **formants** (the resonance pitches of the tube).

The whole question of this project, in instrument terms:

> When my hormones change across the month, do they retune the **reed** (the soft, wet folds) or reshape the **tube** (the throat/mouth cavities)?

The answer turns out to be clean, and it tells me what the driver physically *is*.

---

## What I had to work with (and why it's unusual)

- My **voice**, recorded on 59 days, as a sustained "ahh" and as read sentences.
- My **actual hormones**, measured at home almost every day for two months: **E3G** (a marker of **estrogen**) and **PdG** (a marker of **progesterone**).
- My **body** (Oura ring): temperature, heart rate, heart-rate variability.
- All lined up on the calendar, with two months (January, February) having enough recordings in *both* halves of the cycle to compare fairly.

Why this matters: the most similar published study to mine (Kervin et al., 2025, a daily voice diary across 10 cycles in one singer) said its single biggest missing piece was **measured hormones**. I have them. So in part this is the study that paper asked someone to do.

---

## Finding 1 - The cycle retunes the reed, not the tube

This is the headline. Two pictures tell it.

### 1a. What moves, and what doesn't

![What the cycle moves in the voice](outputs/localization/figures/fig01_localization_map.png)

Each bar is one voice measurement. Bars to the **right** got *higher* in the luteal phase (the second half of the cycle, after ovulation); bars to the **left** got lower. The **grey band in the middle means "too small to matter."**

Read it like this:

- **Blue bars (reed / cover quality)** - these are measures of *how the folds buzz*: breathiness/open-quotient (H1-H2), clarity (HNR), spectral tilt, tone-colour (the timbre/MFCC bars). **Many of these move a lot.**
- **Dark bars at the top (the tube / vocal-tract geometry)** - these are the formants, the shape of the throat and mouth. **They barely move.**

So the change is concentrated in the *reed*, not the *tube*.

**Is "the tube barely moves" real, or did I just get lucky?** I ran a formal test borrowed from single-patient neurology (Crawford & Garthwaite's dissociation test), which asks whether the gap between "reed moves" and "tube stays still" is bigger than chance. Using the five reed/tone-colour measures the earlier studies had already flagged, the gap is real in **both** speaking styles (read sentences: p = 0.008; sustained vowel: p = 0.049). In plain terms: **it is unlikely to be a fluke that the reed moved while the tube held still.**

### 1b. The dog that didn't bark - proving the tube *could* have moved

A skeptic could say: "Maybe your formants never move for anyone - so of course they didn't move across the cycle." So I checked how much my formants move *for reasons that have nothing to do with the cycle*, using the very same recordings.

![The dog that didn't bark](outputs/localization/figures/fig02_sensitivity_floor.png)

Look at F1 and F2 (the two main vowel formants):

- **Within a single sentence**, as I move through different vowels, F1 swings by ~**184 Hz** and F2 by ~**210 Hz**. (Hz = the unit formants are measured in.)
- **Between tasks** (sustained "ahh" vs sentences), they shift by tens of Hz.
- **Across the entire cycle**, F1 moves about **1.8 Hz** and F2 about **5.8 Hz**.

So my measurement easily sees formant movements **20-100 times larger** than anything the cycle produces. The instrument *can* bark - loudly - and across the cycle it stayed essentially silent. That silence is therefore a real clue, not a blind spot. (F3, the third formant, is noisier and moves a bit more; it's the weakest of the three, and I flag it honestly.)

> **Takeaway:** the cycle acts on the soft, wet **cover of the vocal folds** (the reed) and leaves the **shape of the throat and mouth** (the tube) alone. That is exactly what you'd expect if the driver is **fluid and mucus changes in the fold lining**, not a reshaping of the cavities.

---

## Finding 2 - It's progesterone, and it acts in two different places

I measured both hormones daily, so I can ask *which* hormone is pulling the strings - and I can remove a sneaky trap first.

**The trap (and how I avoided it):** earlier I found a tempting "pitch tracks estrogen" link, but it turned out both my pitch and my estrogen were slowly drifting down over the months, so they *looked* connected without being connected. Every hormone result below has that slow drift mathematically removed.

![Which hormone moves each feature, and where it acts](outputs/localization/figures/fig03_two_hormones.png)

**Left panel - which hormone:** red dots (progesterone) sit far from zero for the reed/tone measures (Hammarberg tilt, timbre/MFCC2, clarity/HNR) *and* for a brain-side measure (pitch range). Blue dots (estrogen) hover near zero. **Progesterone is the driver; estrogen is a bystander here.**

**Right panel - where it acts.** This is the genuinely new idea. Progesterone has two known jobs:

1. **Peripheral (in the throat):** it makes the fold lining hold fluid and thickens mucus - directly changing the reed. The "Cover (tissue)" bars show this is almost entirely a **progesterone** effect (progesterone coupling ~0.24 vs estrogen ~0.07).
2. **Central (in the brain):** progesterone turns into a neurosteroid (**allopregnanolone**) that calms brain circuits, including the ones that **control pitch**. The "Pitch control (brain)" bars show this channel responds to progesterone too.

So the cycle isn't just changing the instrument; on the evidence here it's also nudging the **player** - how steadily I control my pitch.

**An honest surprise:** the classic textbook claim is "best voice at ovulation" (when estrogen peaks). I did **not** see that. My voice was actually *clearer* (higher HNR) in the luteal/high-progesterone phase. That contradicts the folklore but matches my own earlier results - and it's a good example of measured data beating a tidy story.

---

## Finding 3 - It's the *rate* of change, not the level

Kervin's 2025 voice-diary study had a striking idea: the voice was most unstable when hormones were *changing fastest*, and calmest when hormones were *flat* - suggesting the voice reacts to the **speed** of hormonal change, not the absolute amount. She could only guess at the speed from the calendar. I can measure it directly from my daily hormones.

![Rate, not level](outputs/localization/figures/fig04_rate_variability.png)

On days when my **progesterone was changing fastest**, my **reed/cover** measures were a bit *more* jittery day-to-day (right-hand bars), while my **tube/geometry** stayed about as steady as ever. It's a modest, directional pattern (I have limited overlapping days, so I'm not over-claiming), but it points the same way as Kervin: **the reed destabilizes when hormones move fast; the tube doesn't care.**

---

## Finding 4 - The premenstrual spike, and why PMDD is the key character

Here's where my own biology matters. **I have PMDD** (premenstrual dysphoric disorder). The modern understanding of PMDD is important and specific:

> PMDD is **not** abnormal hormone *levels*. Women with PMDD have normal hormones. PMDD is an **abnormal brain sensitivity to the normal hormonal shifts** - especially to progesterone's calming metabolite, allopregnanolone, late in the cycle.

In other words, PMDD is a disorder of *over-reacting to the change* - the exact thing Finding 3 is about, but turned up. And critically, it's a **brain** sensitivity - which predicts the effect should show up in the **central, pitch-control** channel, late in the cycle.

![The premenstrual spike](outputs/localization/figures/fig05_premenstrual.png)

Tracking my voice across the late cycle (follicular -> mid-luteal -> premenstrual):

- My **pitch control becomes least steady premenstrually** (red line, pitch variability, jumps up at the end) and my **tone-colour (timbre) peaks premenstrually** (green line).
- Meanwhile clarity and open-quotient peak in the *mid*-luteal phase and then ease off.

So the premenstrual window - exactly when PMDD bites - is where the **brain-side pitch-control** signal spikes. That is the pattern PMDD predicts. It's a small-sample, directional result (the premenstrual days are few), but it's mechanistically pointed, not random.

### How I compare to a normally-cycling singer (Kervin 2025)

Because Kervin's subject does **not** have PMDD (and is a trained singer who may unconsciously compensate), the contrasts are interesting:

- **Glottal opening - we agree.** Her direct throat imaging found *more* glottal opening in the luteal phase; my acoustic open-quotient also rises in the luteal phase. Two completely different methods, same conclusion. That's reassuring.
- **Clarity - we differ.** She found "best voice" near the fertile window; I found my clearest voice in the luteal phase. Could be PMDD, could be training, could be the different measures - I flag it as an open question.
- **Pitch - we differ slightly.** She found pitch highest in the luteal phase; mine dipped slightly. Pitch is exactly the measure most polluted by drift, so I trust this one least.

The honest summary: **where the method is cleanest (glottal opening), an independent study agrees with me; where we differ, it's in the measures most affected by training or drift.**

---

## The body agrees the cycle is real (supporting role only)

I want voice and hormones to be the stars, but it's worth one glance at the body to confirm my cycle labels are trustworthy.

![The body confirms the cycle is real](outputs/localization/figures/fig06_body_context.png)

Body temperature and daytime heart rate rise in the luteal phase (textbook), and heart-rate variability dips. That HRV dip is also a documented feature of PMDD. So the body is doing exactly what a real cycle should - which means the voice findings are anchored to a genuine, well-labeled cycle, not a guess.

---

## So what's the answer?

Putting the clues together, like a diagnosis:

1. **The reed changes, the tube doesn't** -> the driver acts on the **soft, fluid-filled cover of the vocal folds**, not the shape of the throat. (Findings 1)
2. **Progesterone, not estrogen, is the hand on the dial** -> consistent with progesterone's known job of holding fluid and thickening mucus in that lining. (Finding 2)
3. **It acts in two places** - the throat tissue *and* the brain's pitch-control - which is why both my voice *quality* and my pitch *steadiness* move. (Finding 2)
4. **It tracks the speed of hormonal change**, and **spikes premenstrually in the brain-side channel** - exactly the signature PMDD predicts. (Findings 3-4)

In one line: **my voice is a non-invasive readout of how my body - and my brain - respond to progesterone, and it's loudest at the time PMDD is loudest.**

---

## What's solid vs. what's a promising lead

I want to be straight about confidence.

**Solid:**
- The reed-moves / tube-stays-still split (significant in both speaking styles; the "dog didn't bark" check is decisive).
- Progesterone (not estrogen) drives the reed changes, with drift removed.

**Directional / promising leads (not proof):**
- The two-place (throat + brain) story - the brain-side coupling is real but modest.
- "Rate, not level" - points the right way, limited overlapping days.
- The premenstrual/PMDD spike - mechanistically pointed, but few premenstrual days.

**Honest limits:** this is one person (me), with two fully-balanced cycles. Findings are strong *hypotheses about a mechanism*, not population facts. The next step that would change everything is simply **a few recordings in both halves of every cycle**, and more people each compared to themselves.

---

## Why this might matter (the bigger picture)

If a 60-second voice recording can tell you *which* hormone is acting, *where* it's acting (throat vs brain), and *when* you're in your most sensitive window - all without a blood draw - then the voice becomes a cheap, daily, at-home window into hormonal and neuro-hormonal health. For a condition like PMDD, which is invisible on a standard hormone test and defined by *sensitivity* rather than *levels*, a signal that tracks the sensitivity itself could be genuinely useful. That is the "voice as a window into health" idea, made concrete on a single, densely-tracked person.

---

## Mini-glossary (plain language)

- **Source / reed:** the vocal folds - the buzzing source of the voice.
- **Filter / tube:** the throat and mouth - shapes the buzz into vowels.
- **Formant (F1, F2, F3):** the resonance pitches of the tube; they tell you the throat/mouth *shape*. Measured in Hz.
- **Open quotient (H1-H2):** how long the folds stay open each buzz - higher = breathier.
- **HNR (clarity):** how clean vs. noisy the buzz is - higher = clearer.
- **MFCC / timbre:** the overall "tone colour" of the voice.
- **E3G / PdG:** at-home urine markers of **estrogen** and **progesterone**.
- **Luteal phase:** the second half of the cycle, after ovulation, when progesterone is high.
- **Allopregnanolone:** a calming brain chemical made from progesterone; central to PMDD.
- **PMDD:** premenstrual dysphoric disorder - an over-sensitivity of the brain to normal hormone shifts, not abnormal hormone levels.
- **Cliff's delta:** a 0-to-1 measure of how much two groups differ (0.15 small, 0.33 medium, 0.47 large).
- **Drift control:** removing slow month-over-month trends so two things sliding together don't look falsely linked.

---

## Appendix - how to reproduce this

```bash
cd Analysis
source .venv/bin/activate
python -m src.analysis.localization.run       # writes all tables + summary.json
python -m src.analysis.localization.figures   # writes fig01..fig06
```

Code lives in `src/analysis/localization/` (one job per file):

- `config.py` - the feature groups (reed/cover, timbre, pitch, central control, geometry) and the hormone predictions
- `dataset.py` - builds the daily table and the within-cycle normalization
- `dissociation.py` - Finding 1: the reed-vs-tube dissociation test + equivalence test
- `sensitivity.py` - Finding 1: the "dog that didn't bark" formant-movement check
- `hormones.py` - Finding 2: estrogen vs progesterone attribution + the two-pathway split
- `rate_variability.py` - Finding 3: variability vs the speed of hormonal change
- `pmdd.py` - Finding 4: the premenstrual window, the Kervin comparison, and the body context
- `run.py` / `figures.py` - run everything and draw the pictures

Tables: `outputs/localization/tables/`  ·  Figures: `outputs/localization/figures/`

## Further reading (the shoulders this stands on)

- Kervin et al. (2025), *Daily Laryngeal Kinematics and Acoustics Throughout the Menstrual Cycle* - the closest prior study; asked for measured hormones.
- Crawford & Garthwaite (2005) - how to test a dissociation in a single case.
- Lakens (2018) - equivalence testing (how to show something is *flat*, not just unproven).
- Abitbol et al. (1999) - estrogen vs progesterone effects on the vocal-fold lining.
- Zhu et al. (2016) - progesterone/allopregnanolone and the brain's control of vocal pitch.
- Timby et al. (2025) and the allopregnanolone/GABA-A account of PMDD.
