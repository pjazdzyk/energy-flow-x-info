# Corrections

Corrections that changed a result a user may have relied on, newest first. Open defects are listed on
[energyflowx.com/known-issues](https://energyflowx.com/known-issues) until they are fixed.

## 2026-10-26 · Heat recovery with a Preheater: a supply target inside the preheater's jump is now met

A heat recovery target mode with a Preheater whose trigger lies below its target (for example -3 / +5 °C) treated the preheater as a switch with no memory. It came on only where the unprotected wall fell below the trigger, and then it lifted the wall straight to its target. So the supply leaving the exchanger jumped at that rating, and a supply target inside the jump could not be met. On the calculator's default network at -15 °C, the supply jumped from about 7.5 to 13.0 °C. A target of 12 °C answered out of reach at 13.0 °C, and a target of 10 °C never settled and ran out of the 30 s limit.

The preheater now behaves like a controller with a differential. Between its trigger and its target, both states are valid. A target mode first looks for the target with the preheater off, then with it held on. On the same network, targets of 10 and 12 °C are now met with the preheater held on. The device says so, and it names the jump and both its sides for a target that still falls inside one, as on an enthalpy core.

Only supply targets inside a preheater's band moved, from out of reach to met. Effectiveness mode, every other target and every other frost strategy give the same answers as before. The change reaches the Heat Recovery calculator, the REST API and the MCP air tool `calculate_air_process`. If you used a Preheater target answer that read out of reach, or that failed with a time limit, calculate it again.

## 2026-10-26 · Hydraulic network API: a relief valve below its set pressure is shut

In the REST hydraulic network API (`/api/v1/process/hydraulic/solve` and `/report`), a relief regulator below its set
pressure was answered wide open, so the bleed it guards carried a large flow and the network around it was solved
with that flow. A relief valve below its set pressure is shut and passes only its seat leakage. It now answers so,
and above its set pressure it holds its set pressure. A relief whose section is not its own two ends is refused with a
named reason instead of being solved as a pressure controller across that section.

The design builder, which draws relief valves, is not released, and the MCP tools did not solve a relief valve, so
only a direct call of the REST API with a relief regulator was affected. If you sent one, solve it again.

## 2026-10-26 · Cooling coil, dehumidifier, steam humidifier and compressor: a root search that left its range

Several devices find their outlet by searching for a root inside a known range. The search could step outside that range. Then it either returned a value outside it, or it failed on a request that has an answer. Every root search now stays inside its range, and a coil outlet is checked against the coil before it is reported.

- **Cooling coil and dehumidifier with a target relative humidity a little above the inlet's.** One case returned an outlet colder than the coolant and much too dry, and reported it as feasible. Example: inlet 26.85 °C with 18.55 g/kg, coolant 6.98 / 9.55 °C, target 83.8 %. The outlet came out 21.9 K too cold at 4.34 g/kg, where the right outlet holds 18.17 g/kg. Targets a little higher, such as 84.5, 85 and 90 % on the same inlet, failed with an error. They now answer 17.96, 17.80 and 16.22 g/kg.
- **Steam humidifier.** Some targets on a valid range failed with an error, and they now answer. Steam added to air colder than about -5 °C, where the fog would settle below the model's liquid range, used to return an outlet that did not conserve energy, sometimes with negative fog. It is now refused with a reason.
- **Compressor with a fluid from the registry.** Some discharge states failed, or came from a search that had not settled. They now answer. One example is dry air from 1.12 bar and 31.5 °C to 2.18 bar, which reported no power and now gives 369.25 kJ/kg. A discharge exactly at a phase change is answered from the side that meets it.

Every other answer is unchanged, to the last digit, on our reference sets. The service does not store calculator results. A value you copied from the Cooling, Dehumidification, Steam Humidification or compressor calculations, the REST API or the MCP air tools before this date, for one of the cases above, should be calculated again.

## 2026-10-26 · Natural gas: viscosity and thermal conductivity follow the methane reference

The viscosity and thermal conductivity of natural gas now come from extended corresponding states with methane as
the reference fluid, using the published methane viscosity of Sotiriadou and co-authors (2025) and the methane
thermal conductivity of Friend, Ely and Ingham (1989). Pure methane now agrees with both within 0.031 % for
viscosity and 0.026 % for conductivity. Before, the earlier gas correlations read pure methane up to 12 % high in
viscosity at 600 K and up to 5 % low in conductivity.

For typical natural gases the change is −10 to +2 % in viscosity and −2 to +5 % in thermal conductivity. A pipe
carrying a gas of 95 % methane at 10 °C sees its viscosity fall by 1.5 % and its pressure drop by 0.3 %.

These values reach the Natural Gas calculator, its property tables, the REST API, the MCP tool
`get_natural_gas_properties` and every natural-gas pipe in a network run. If you used a natural-gas viscosity,
thermal conductivity, Prandtl number or a gas pipe's pressure drop from before this date, calculate it again.

## 2026-10-25 · Humid air: thermal conductivity, Prandtl number and thermal diffusivity corrected

The thermal conductivity of humid air was too high, and the error grew with temperature and humidity. The Prandtl
number was too low and the thermal diffusivity too high by the same share. The mixing rule now follows the published
Wassiljewa form with the Mason and Saxena factor, built from the pure components' dilute viscosities. It reproduces
the worked examples of the textbook method. Dry air and the viscosity of humid air did not change.

Thermal conductivity at 101.325 kPa, change against the earlier value:

| State | Change |
|---|---|
| 25 °C, 10 g/kg | −1.9 % |
| 25 °C, 15 g/kg | −2.7 % |
| 40 °C, 30 g/kg | −5.1 % |
| 60 °C, 100 g/kg | −12.8 % |
| 80 °C, 300 g/kg | −22.0 % |
| 100 °C, 500 g/kg | −24.8 % |

The thermal conductivity of the refrigerant blend R-454B also changed, by about +1 % in the vapour and by less than
0.15 % in the liquid. The other blends did not change.

These values reach the Humid Air calculator, its property tables, the REST API and the MCP tool
`get_fluid_properties`. If you used a humid-air conductivity, Prandtl number or thermal diffusivity from before this
date, especially above 40 °C or 30 g/kg, calculate it again.

## 2026-10-25 · Heat recovery: energy books close near a 0 °C exhaust, target modes never claim a missed target, and frost protection stops where frost can no longer form

Heat recovery results changed on the website, the REST API and the MCP server:

- **Energy books near a 0 °C exhaust.** Where the exhaust leaves the exchanger at 0 °C with its condensate freezing
  only in part, the energy balance now closes. Before, it could be open by up to 1.3 kW.
- **Target modes.** A supply temperature or recovered power target that the exchanger cannot reach is now reported as
  not feasible, at the closest value the exchanger delivers and at the lowest rating that delivers it. Before, a target
  mode with frost protection could report a target as met while missing it by up to 5.6 K, or miss a reachable target.
- **Frost protection stops where frost can no longer form.** A bypass or preheater now lifts the coldest wall to its
  trigger or target, or only as far as the wall at which the exhaust vapour stops reaching it, when that is lower. No
  frost forms past that point. With dry exhaust air the bypass opens less, or the preheater adds less heat, than
  before, and the outcome reads `PROTECTED` with the wall it reached, which can be below the trigger.
- **Exact outlet temperatures.** An air stream that leaves the exchanger dry now has its temperature read exactly
  from its enthalpy and humidity ratio. Reported temperatures moved by up to 0.02 K, and bypass or preheater results
  by up to about 60 W.
- **Summer second law.** A sensible exchanger in summer no longer sends an outlet warmer than the hottest inlet.

If you used a heat recovery target mode, a frost protection result with dry exhaust air, or the energy balance of a
case with the exhaust near 0 °C from before this date, calculate it again.

## 2026-10-25 · Heat recovery: frost risk follows the physics, and frost protection solves correctly

Heat recovery frost results changed on the website, the REST API and the MCP server:

- **Frost risk** is now reported when the coldest exchanger wall is at or below 0 °C and the exhaust can deposit
  vapour on it, whatever trigger is set. Before, the verdict followed the trigger, so with the default trigger of
  −3 °C a wall between −3 and 0 °C was reported free of frost although condensate freezes there.
- **The default trigger is 0 °C**, where condensate freezes. It was −3 °C.
- **The wall near 0 °C.** Where condensate freezes only in part, the wall now holds at 0 °C. Before, it could jump
  by up to 0.08 K across 0 °C.
- **Reversed flow.** With one air stream reversed, the wall is the colder end of the core and the bypass follows the
  parallel-flow relation. Before, the wall read several kelvin too cold and could report frost on a core above 0 °C.
- **Exact walls.** A bypass or preheater that holds its goal reports the goal exactly. A bypass at a 0 °C trigger
  showed −9.1e-11 °C.
- **Preheater speed.** A Preheater case that ran out of the 30 s limit now answers in a few seconds. Its numbers
  moved by less than 1e-5 K.
- **New result.** Each result states the outcome of frost protection (`frostProtectionOutcome`): protected, held
  below freezing, not engaged, at its limit, out of range, and so on.

If you relied on a frost verdict or a defrost result from before this date, especially one with a trigger below
0 °C, calculate it again.

## 2026-10-17 · Duct sizing: two duct series withdrawn

Two duct series were withdrawn from the catalogue:

- the thick-wall PVC series CHWENT_P_PVC_CIRC_TCK,
- the rectangular series AWENT_F_TPF_RECT.

The duct tool now answers a request for either series with not found. If you sized a duct from either series, check
the size against the maker data of the duct you intend to install.

## 2026-10-17 · Compressed-air treatment: the water rank uses a new scale

The water rank of compressed air was renumbered on purpose, when the water grading moved to our own scale of
dew-point bands. For the same air the rank now reads one lower:

- discharge air: 7 became 6,
- ambient, aftercooler and separator outlets: 6 became 5,
- a dryer at +3 °C pressure dew point: 4 became 3.

A result, report or saved study made before the change shows the old numbers, so do not compare ranks across the two.
