# Elements, Solar module: clear sky irradiation evidence

This folder holds a reproducible comparison of the Elements **Irradiation** metric, the optional
kWh/m² figure the Solar tool can report alongside direct sun hours, with the clear sky
irradiance published by the EU Joint Research Centre in PVGIS.

It is the companion to the [direct sun hours evidence](../README.md) one level up. That case
compares the geometry. This one compares the energy model layered on top of it.

---

## 1. What is being compared, and what is not

The Irradiation metric estimates **clear sky potential**: how much solar energy a surface would
receive under a cloudless sky, from a weather free model. It is not measured yield, it is not a
TMY based estimate, and it does not account for cloud. The tool labels it that way on every view,
and this folder does not claim otherwise.

The model is **Bird and Hulstrom (1981)**, a published clear sky model from
SERI (now NREL), freely available with attribution as published. Two separate things have to be right for the reported number to be right:

1. **The instantaneous model.** Does the code reproduce Bird and Hulstrom's own worked table?
   That is compared with the published table, within the stated tolerance, in the product's live
   comparison report and in its unit tests. It is not what this folder is about, because a model
   agreeing with its own source paper is an implementation check, not an independent one.
2. **The integration.** The number a user sees is a whole year accumulated. Integrating a correct
   instantaneous model incorrectly is easy to do and hard to see. It produces a plausible figure that
   is wrong. **That is what this folder checks**, against a different model built by different
   people.

---

## 2. The reference, and why it is a ballpark check

**PVGIS** (EU Joint Research Centre) is a free and open solar resource tool. Its clear sky
irradiance comes from the **McClear** model, using the CAMS aerosol climatology. Bird and McClear
are different formulations with different aerosol treatments, so:

> Two different clear sky models should land within a few percent of each other, **not** match
> exactly. An exact match between Bird and McClear would be the tell of a fudged comparison,
> not a good result.

The percentage is therefore the weaker half of this evidence. **The stronger claim is the
bracketing.** The tool exposes a single **Clarity** knob with three presets, and the Clean and Hazy
presets must *straddle* the PVGIS value at every site. That shows the knob spans a physically
reasonable range of atmospheres, rather than the Average preset having been tuned to hit one
number, which a percentage on its own cannot distinguish.

---

## 3. Method

| | |
| --- | --- |
| Quantity | Annual clear sky **global horizontal** irradiation, kWh/m² |
| Surface | Flat, unobstructed sensor, the simplest apples to apples comparison |
| Year | 2023 |
| Ours | Bird and Hulstrom 1981, integrated over the whole year with the tool's own NOAA solar position math, at Average clarity, plus the Clean and Hazy presets for the band. Fully offline. |
| Reference | PVGIS v5.2 `DRcalc` clear sky output `Gcs(i)` (W/m²): the average day hourly clear sky global irradiance per month, integrated to a daily total, weighted by days in month, summed to annual. |

Three sites, chosen to span latitude, altitude and climate rather than to flatter a model:
Warsaw (52.23 N, 119 m), Madrid (40.42 N, 667 m) and Rome (41.90 N, 21 m).

---

## 4. Result

| Site | PVGIS clear sky (McClear) | Ours, Average | Difference | Ours, Clean to Hazy band | PVGIS in band |
| --- | --- | --- | --- | --- | --- |
| Warsaw (52.23, 21.01, 119 m) | 1607.3 kWh/m² | 1652.7 kWh/m² | **+2.8 %** | 1336 – 1751 | yes |
| Madrid (40.42, −3.70, 667 m) | 2080.8 kWh/m² | 2032.4 kWh/m² | **−2.3 %** | 1687 – 2147 | yes |
| Rome (41.90, 12.50, 21 m) | 1953.7 kWh/m² | 1981.8 kWh/m² | **+1.4 %** | 1641 – 2092 | yes |

The two models differ by at most **2.8 %** at the three sites, and the PVGIS value
falls inside our Clean to Hazy band in every case. The residual is the expected spread of two
different clear sky formulations, and of our single Clarity knob against PVGIS's location specific
aerosol climatology. It is not an error term.

This is a comparison of two models at three sites. It is not an energy yield assessment and not a
design certification, and the results are for review by a professional engineer, who remains
responsible.

### The integration step is checked, not assumed

The year integrates at an hourly step for cost. A coarse step chosen for speed and never checked
is how an integration error hides, so the product's suite carries the hourly total
against a ten minute one as a row of its own: they agree to about **0.002 %**, four orders of
magnitude inside the percent level agreement this comparison is about.

### Re-run

Recorded **2026-06-21**. Both sides were re-run on **2026-09-07**: the PVGIS reference was
re-fetched from the live service and came back identical to the recorded figures, and again on
**2026-10-25** with the same result. Our side is
recomputed from scratch on every run of the product's test suite and on every load of the
comparison page.

---

## 5. Reproduce it yourself

### A. The reference (PVGIS)

No dependencies beyond Node 18 or newer, and a network connection:

```bash
node scripts/pvgis_reference.mjs
```

It queries the PVGIS `DRcalc` endpoint month by month, integrates the clear sky series, and prints
the annual figure per site, then the same rows in the exact format of `scene/pvgis-reference.csv`
so you can diff your run against the recorded reference:

```bash
node scripts/pvgis_reference.mjs | sed -n '/csv form/,$p' | tail -n +2 > mine.csv
grep -v '^#' scene/pvgis-reference.csv | diff -u - mine.csv    # no output = identical
```

To check a figure by hand instead, open the PVGIS
[Daily radiation](https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis/pvgis-tools/daily-radiation_en)
tool, enter the latitude and longitude, tick **Clear-sky**, and read `Gcs` for each month.

**The script deliberately computes only the reference half.** A comparison script that computes
both columns and is committed next to its own output can no longer fail. Our column comes from the
product, independently, below.

### B. EnergyFlowX, headless (the product's test suite)

The clear sky model and the solar position math are pure, dependency free kernels, so a whole year
integrates outside the browser in a fraction of a second. The product's own test suite, which is
not public, integrates the year from scratch on every commit, compares it against the recorded
PVGIS figures, asserts the bracketing at every site, and checks the integration step against a
finer one. Route C below is the public route.

### C. EnergyFlowX, in your browser

Open the Elements comparison report and read **Pillar 04, Clear sky irradiance**. Our column there
is integrated live in your browser on page load, from the same kernel the tool uses, so it cannot
show a stale number. Only the PVGIS column is recorded.

---

## 6. Files in this folder

```text
clear_sky_irradiation/
  README.md                        this document
  scene/
    pvgis-reference.csv                the reference result, machine readable
  scripts/
    pvgis_reference.mjs                fetches and integrates the PVGIS reference
```

---

## 7. Licensing and attribution

- **Bird, R. E. and Hulstrom, R. L. (1981)**, *A Simplified Clear Sky Model for Direct and Diffuse
  Insolation on Horizontal Surfaces*, SERI/TR-642-761. A report of the United States Government
  (SERI, now NREL).
- **PVGIS**, European Commission Joint Research Centre. Named here for comparison only and not
  affiliated with EnergyFlowX. The PVGIS clear sky figures in this folder are not bundled into the
  application, and nothing of the PVGIS source, interface or documentation is reproduced here. The
  typical meteorological year that Elements offers as measured weather is a separate PVGIS service,
  credited in the root README.

EnergyFlowX, Elements and the Solar tool are the property of Synerset. See the repository root
for the full license and citation terms.
