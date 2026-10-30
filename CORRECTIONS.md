# Corrections

Corrections that changed a result a user may have relied on, newest first. Open defects are listed on
[energyflowx.com/known-issues](https://energyflowx.com/known-issues) until they are fixed.

## 2026-10-31 · Humid air in fog: the partial pressure of water vapour

In fog (more water than the air can hold as vapour) the partial pressure of water vapour was computed from all the water, the condensed droplets included, so it read above the saturation pressure, which no vapour can exceed. At 1 atm and 20 °C with a humidity ratio of 20 g/kg it read 3.156 kPa, where the vapour's partial pressure is 2.349 kPa, and the error grew with the amount of water: at 1 kg/kg it read 62.5 kPa. Only the vapour exerts a partial pressure, so in fog it is now the saturated value at the state, however much water is suspended, and it joins the unsaturated values smoothly at saturation. No other property changed: every other humid-air property already used the saturated vapour in fog, and air below saturation is unchanged to the last digit.

This reaches the humid air calculator, the property tables, the REST API and the MCP tools `get_fluid_properties` and `get_property_table`. If you used the water vapour partial pressure of fog, read it again.

## 2026-10-31 · Hydronic runs over time: every step closes its vessel balance, or says it did not

A run over time solves each time step implicitly: the pressure of each vessel (an expansion vessel, a receiver, a tank) at the end of the step must agree with the flow into it over the step. Near a source's pressure, where the driving pressure is small, and in stiff steps, the solver could end a step without that balance closing. It warned that steps did not close, and the run went on from a state off the true answer by up to 12 kPa in a test run. With two or more vessels, an intermediate fix could even report such steps as closed.

A step now counts as closed only at a solve where every vessel's balance is within its tolerance, and the step commits that solve. Several vessels are closed together. A step that still cannot close is named in the warning. In test sets of air receivers and expansion vessels, every run that had unclosed steps now closes them, and runs that closed before are unchanged with one vessel and move by at most 1.1 Pa with several.

If you used a run over time whose reply warned that steps did not close their implicit balance, its pressures, flows and vessel trajectories moved. Run it again.

## 2026-10-30 · Humid air, R-32 and R-454B, helium and steam: property corrections

**Humid air.** Its properties are now derived from one description of the mixture, the same one its enthalpy already used. Before, the entropy left out the air-water interaction term the enthalpy carried, the density came from a different formula, and the heat capacity at constant volume subtracted a gas constant on a different mass basis than the one it was subtracted from. As a result moist air read a lower speed of sound than dry air, where it is higher. At 1 atm the heat capacity at constant volume moves by 0.3 to 1 %, the ratio of heat capacities and the speed of sound by 0.1 to 1 % (25 °C at 55 % RH: speed of sound up 0.30 %), and the density by a few parts per million. Enthalpy, heat capacity at constant pressure, wet bulb and dew point did not change. At high pressure the moves are larger (at 5 MPa density up to 1 %, entropy up to 8 J/(kg·K)). Air at zero humidity now gives the dry-air values exactly: at 5 MPa and -45 °C its heat capacity at constant volume read 894 J/(kg·K) and is 742.
In fog (more water than the air can hold as vapour), the heat capacity at constant pressure now includes the evaporation of the suspended water: at 20 °C and a humidity ratio of 0.02 it reads 3.35 kJ/(kg·K), where it read 1.06. Properties that are not defined for a two-phase state (heat capacity at constant volume, speed of sound, compressibility factor and the compressibilities) are now refused with the reason, where they read values that could be negative. Dry air now has a wet bulb (5.81 °C at 1 atm and 20 °C), and its dew point is refused, since it has no water vapour.

**R-32 and R-454B thermal conductivity.** R-32 conductivity is now given from its triple point (-136.8 °C), where it was refused below -23.15 °C. Below 250 K the dense part follows a published correlation and the dilute-gas part a standard kinetic-theory shape anchored to our fit at 250 K, joined smoothly to the fit, which is unchanged from 250 K up. R-454B, which takes R-32's dilute-gas term, moved below 250 K: its vapour conductivity is up to 5.6 % lower at 200 K, its liquid up to 0.23 %. R-454B, R-410A and R-407C transport below their component correlations' lower limits (220, 250 and 250 K) now carries a warning.

**Helium** thermal conductivity, thermal diffusivity and Prandtl number are refused above 100 MPa, beyond the stated validity of the correlation, which turns negative at high pressure.

**Steam** given by enthalpy and entropy near freezing, and steam below the triple-point pressure (611.2 Pa), now answer where they were refused.

These reach the fluid property calculators, the property tables, the air-process calculators, the REST API and the MCP tools `get_fluid_properties`, `get_saturation_properties`, `get_property_table` and `calculate_air_process`. If you used a speed of sound, heat capacity ratio or compressibility of humid air, a property of fog, or an R-454B vapour conductivity below -23 °C, calculate it again.

## 2026-10-30 · Hydronic: a design or balance stopped by its time limit no longer reads as a pass

A design run chooses each radiator valve's dial and resizes runs in passes, and a light air network call searches for its target flows. These searches were bounded partly by computing time. On a busy server a search could stop early and still answer CONVERGED, with a validation that read as a pass beside a radiator left short of its output. In a test circuit one radiator read 3.5 % short this way, while the same request on a quiet machine met every output.

The searches are now bounded by a count of work, so the same request gives the same answer whatever the load. Where the time limit still stops a run, the reply says so: the status reads TARGETS_MISSED, the design validation reads INCOMPLETE and names each radiator or run left unmet, and the report's headline says it is not the design's answer. A light air calculation that runs past 30 s is refused with a sentence on how to ask again, never answered with numbers cut short. This applies to `hydronic_solve`, `hydronic_report` and the REST design, balance and report endpoints.

If you used a design or balance whose status read CONVERGED during a busy period and a radiator later read short, run it again.

## 2026-10-30 · Hydronic over REST: a run over time now holds its regulators

A REST run over time on a design with pressure-independent control valves, differential pressure controllers, constant air volume dampers or pressure regulators solved the network with those elements at a fixed resistance. The regulators were ignored without a word. They are now held at every step, as in a steady solve, and the reply states the regulation band (5 % by default). Over MCP the same run was refused before and now runs.

If you used a REST run over time with regulators in the network, its flows, pressures and vessel trajectories moved. Run it again.

## 2026-10-30 · Hydronic and air processes: humid air with the corrected fluid properties

The humid air corrections of the same day (heat capacity at constant volume, speed of sound and compressibility, and air with fog) reach Hydronic ventilation networks and the air treatment processes. Pressure losses and flows of humid air ducts moved by a few parts per million through the density. In a compressed humid air network whose air holds more water than it can carry as vapour (fog), the speed of sound is no longer reported, because it is not defined there. Air treatment results moved where they read a heat capacity in fog.

## 2026-10-30 · Fluid density: a pure fluid near its saturation line now returns the stable phase

The density of a pure fluid below its critical temperature is found by solving its equation of state for the density that gives the stated pressure. Near the saturation line that equation has two physical roots, liquid and vapour, and the solver could return the wrong one with no warning:

- **Compressed liquid returned as vapour.** Just above the saturation pressure, the solver slid onto the vapour root and never looked for the liquid. Nitrogen at -183.16 °C (89.99 K) and 3.96 bar read 16.8 kg/m³; the liquid there is 745 kg/m³. Hydrogen at 15 K and 0.3 bar read 0.514 kg/m³ instead of 76.2. Propane, methane and R-1234ze(E) showed the same at a few states each.
- **A root inside the two-phase region.** Close to the saturation pressure the solver could accept a density that lies inside the two-phase region, which is neither phase. Argon at 138.251 K and 29.38 bar read 514.5 kg/m³, labelled vapour; the vapour there is 161.6 kg/m³.

The solver now finds the vapour root and the liquid root each on its own branch, checks that each belongs to its phase, and returns the one that is stable. In a check over 45,000 states of all pure fluids, the 156 that changed were all wrong before, and every other state is unchanged to the last digit. Mixtures (refrigerant blends and natural gas) use a different path and did not change.

This reaches every property of the pure industrial gases and pure refrigerants that depends on density (enthalpy, entropy, heat capacities, speed of sound, viscosity, conductivity), in the fluid property calculators, the property tables, the REST API, the MCP tools `get_fluid_properties` and `get_property_table`, and Hydronic networks that carry a pure fluid. If you used a pure fluid's properties within a few percent of its saturation pressure, calculate them again.

## 2026-10-30 · Fluid transport properties: cold nitrous oxide gas, and R-1234yf and R-32 near their triple points

**Nitrous oxide gas below about -55 °C.** Its viscosity and thermal conductivity are computed by mapping each state onto nitrogen. For cold gas that mapping has no exact solution, and the solve returned a diverged state instead of saying so. Viscosity came out two to four times too high, and at some states thousands of times: at -59 °C and 4 bar it read 0.173 Pa·s, at -70 °C and 1 bar 2.09e-5 Pa·s, and on the saturated vapour at -60 °C 2.35 Pa·s. The gas there has a viscosity of about 1.0e-5 Pa·s. The mapping now accepts only a converged, physically valid state and otherwise uses the low-density form the method publishes. The examples now read 1.08e-5, 1.01e-5 and 1.08e-5 Pa·s. Liquid and supercritical nitrous oxide did not change, and warmer gas changed by less than 1 %.

**R-1234yf and R-32 at their coldest states.** Two R-1234yf correlations were evaluated below the 220 K their sources state, and they cross zero near 126 K. Saturated vapour near the triple point read a negative viscosity (-2.8e-7 Pa·s at 123 K) and a negative conductivity, and values up to about 160 K were far too low. The R-32 liquid conductivity was evaluated below the 250 K its fit covers and fell as the liquid cooled, the wrong direction (0.141 W/(m·K) at 137 K against 0.203 at 186 K). Point calculations and pressure-temperature tables already refused below those limits, the saturation tables did not. A table row below a limit now leaves out that column and keeps every other property. Values above the limits are unchanged.

These reach the fluid property calculators, the property tables, the REST API and the MCP tools `get_fluid_properties`, `get_saturation_properties` and `get_property_table`. If you used a viscosity, conductivity, Reynolds or Prandtl number of nitrous oxide gas below about -55 °C, or of R-1234yf or R-32 near their triple points, calculate it again.

## 2026-10-30 · Hydronic design: a dial raise that does not help is undone, and a stated margin is met

Since 2026-10-28 a design raised the valve of a radiator short of its output one dial position at a time. When the radiator was too small for its supply, the raise was judged ineffective and still kept, so the circuit took more flow and its return ran warmer, while the radiator stayed short. A raise that does not lower the shortfall is now undone, and the reply names the remedy, a larger radiator or a warmer supply. And with an emitter margin stated, the dials now aim at the margined output, so a 5 % margin is delivered instead of being absorbed by the validation line.

Dials, flows and outputs of designs with a radiator too small for its supply, or with a stated emitter margin, moved. Balance such a design again.

## 2026-10-28 · Hydronic design and balance: valve dials chosen for the radiators' output

A balanced heating design rounded each radiator valve's setting to the nearest dial position. Under a pump with head to spare, rounding down left radiators short of their output: in a six-radiator test circuit two read 5.2 to 5.7 % short, and with a 5 % emitter margin three read 5.1 to 8.4 % short, so the design failed its own emitter check. The report's headline still said every run and node met its criteria.

A valve whose rounded dial would leave its radiator short of the output it must give is now set one position up, predicted from the radiator's own law and checked with a solve. Only a radiator still in deficit after that gets further raises, and a raise stops when more flow no longer adds output. Then the reply names the remedy, a larger radiator or a warmer supply. The same choice is made by the Hydronic MCP balance and by the REST report. The report headline states the design validation verdict, and a radiator in deficit at its dials reads `TARGETS_MISSED`.

Dials, flows and outputs of balanced heating designs moved. If you used a balance or design whose validation read FAIL on emitter output, or a REST report's commissioning sheet, balance it again.

In the same release, a run over time's sampled table and chart show each interval's lowest and highest value, so a cycle as long as the row spacing no longer reads as a slow trend, and an unloaded compressor no longer passes air backwards or warns that it does.

## 2026-10-27 · Hydraulic networks: an answer that cannot be used no longer reads converged

A hydraulic solve reported `converged: true` and `status: CONVERGED` whenever its numerical iteration settled, even when the answer it settled on could not be used. Three cases:

- **Flow targets that cannot all be met.** In the REST hydraulic network API (`/api/v1/process/hydraulic/solve` and `/report`), a design with two or more flow targets ran a fixed number of sweeps and returned the last one as converged, with a target missed. Example: two targets on series runs that read the same demands, 105 m³/h asked and 118.9 m³/h delivered, a miss of 13.2 %. It now answers not converged with `TARGETS_MISSED` and names each missed target. A single target whose search closes on a jump of the flow is treated the same way.
- **A state that does not exist.** A node at or below zero absolute pressure, or a liquid that boils at the pressure it was solved at, read `CONVERGED` with warnings beside it. Example: two parallel pipes asked for 15 kg/s solved to -831.6 kPa absolute. It now reads `NOT_PHYSICAL`, over MCP and REST alike, and REST lists the phase problems as MCP does.
- **A balance that missed its targets.** A Hydronic balance whose valves could not reach their design flows read `CONVERGED`. It now reads `TARGETS_MISSED`, with the misses listed.

In every case `converged` is now true exactly when `status` is `CONVERGED`, and the solver's own result is kept in `solverStatus`. No number moved. If you relied on a converged answer from one of the cases above, solve it again and read `status`.

In the same release, Hydronic sizing stopped calling a run infeasible when it missed only a minimum velocity that no size of its series reaches, or reaches only by breaking a ceiling. The size it chose is unchanged. The reply now says which of the two it is.

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
