# Hydronic, pipe heat loss to the air around a run

This folder holds a comparison of the pipe heat loss in Hydronic (REST and the members MCP server) with a
separate calculation written from the published correlations. The script is Python, uses the standard library
only, shares no code with the product and prints each case beside the figure the server returned.

A run of pipe can lose heat to the air of a zone it passes through. The loss goes through the inside film, the
pipe wall, each insulation layer and the outside film. The outside film is natural convection, crossflow of the
wind, or both, plus radiation to the zone. The outlet temperature follows from the loss.

## 1. What is compared

Three requests, in [requests](requests). Each is the JSON body of a Hydronic design with one run, and each
sets the run's zone, wall and insulation.

| Case | Run | Air |
| --- | --- | --- |
| A | Bare steel DN50 (52.5 mm bore, 3.9 mm wall), 20 m, water at 70 oC | Still room air at 20 oC |
| B | The same run with 40 mm of mineral wool | Still room air at 20 oC |
| C | Bare steel DN25 (26.6 mm bore, 3.2 mm wall), 40 m, water at 70 oC | Outdoors, 3 m/s wind, a zone schedule: 0 oC to 300 s, then -10 oC, over 600 s in 60 s steps |

The figures compared are the heat loss, the loss for each metre, the conductance (UA), the outlet and surface
temperatures, and for case C the energy lost over the run.

The mass flow of each run is an input of this comparison. It is the flow the server's hydraulics found for the
pressure difference in the request, and it is stated in the script. The hydraulics is not under test here.

## 2. How the reference is computed

`pipe_heat_loss_reference.py` computes each case in the same order as the physical path of the heat:

1. The run is taken at its mean stream temperature, and the outlet follows from the exponential approach to the
   air temperature with the run's conductance. Outlet and mean are iterated together.
2. For a trial surface temperature the heat flow per metre leaves through the outside film (convection plus
   radiation).
3. The same flow is walked inward through each layer. A layer's conductivity is taken at the mean of its two
   face temperatures, from the conductivity points of its material.
4. The inside film then gives the stream temperature that this surface temperature implies.
5. The surface temperature is found by a root search (bisection) so that the implied stream temperature is the
   mean stream temperature.

The films are, by name: the Gnielinski form inside (with the friction factor of the rough pipe from the
Colebrook form, and a linear blend between laminar and turbulent from Re 2300 to 4000), the Churchill and Chu
form for natural convection on a horizontal cylinder, the Churchill and Bernstein form for crossflow, the two
combined as the cube root of the sum of cubes, and grey radiation to surroundings at the air temperature.

**Inputs and their basis** (all stated in the script):

- Liquid water, every 10 K from 0 to 100 oC: density, specific heat, conductivity and viscosity from the IAPWS
  formulations, rounded.
- Dry air: ideal gas density, a constant specific heat of 1006 J/(kg K), and Sutherland's law for viscosity and
  conductivity.
- Materials: the steel (50 W/(m K), emissivity 0.85) and the mineral wool (0.037, 0.042 and 0.052 W/(m K) at 20,
  50 and 100 oC, emissivity 0.9) are the materials stated in the requests, not catalogue values.
- Pipe roughness 0.045 mm, as in the requests.

The reference holds no factor that was set to bring it toward the server's figures. The gaps below are what two
independent implementations of the same named methods leave.

## 3. Re-run it

```text
python3 -I pipe_heat_loss_reference.py
```

It needs Python 3 and nothing else (run here with 3.12). It prints the table below and writes
`expected_figures.json`, which holds the reference value, the recorded server value and the gap for each
figure. The server values are recorded in the script. To re-run the server side, post the files in
[requests](requests) to the Hydronic solve of the REST API with your account's key and read the heat loss of
the run `main`, or build the same design in a Hydronic session and read `data.thermal.distribution`.

## 4. Result

Gap = (server - reference) / reference. Run of the script with the inputs above:

| Case | Figure | Reference | Server | Gap |
| --- | --- | --- | --- | --- |
| A | Heat loss | 2306.3 W | 2308.3 W | +0.09 % |
| A | Loss for each metre | 115.32 W/m | 115.41 W/m | +0.09 % |
| A | Conductance | 46.61 W/K | 46.65 W/K | +0.09 % |
| A | Outlet / surface | 68.965 / 69.071 oC | 68.963 / 69.071 oC | -0.001 K / +0.001 K |
| B | Heat loss | 283.3 W | 284.2 W | +0.33 % |
| B | Loss for each metre | 14.16 W/m | 14.21 W/m | +0.33 % |
| B | Conductance | 5.672 W/K | 5.691 W/K | +0.33 % |
| B | Outlet / surface | 69.873 / 24.008 oC | 69.873 / 24.016 oC | -0.000 K / +0.008 K |
| C | Heat loss, air -10 oC | 10496.7 W | 10525.3 W | +0.27 % |
| C | Heat loss, air 0 oC | 9230.7 W | 9251.8 W | +0.23 % |
| C | Conductance, air -10 oC | 154.28 W/K | 154.78 W/K | +0.32 % |
| C | Outlet, air -10 oC | 47.329 oC | 47.257 oC | -0.073 K |
| C | Energy lost over 600 s | 1654.5 Wh | 1658.7 Wh | +0.25 % |

What the gaps resolve: the largest is 0.33 % of the loss and 0.07 K of an outlet temperature. The server is
higher than the reference in every case. The cause of the remaining gap is not isolated. The two
implementations differ in property data and in how the correlations are combined, and this comparison does not
separate those. It says nothing about any other pipe, fluid or zone.

## 5. Limits

- **One ambient for each run.** A zone has one air temperature at a time. The mean radiant temperature equals
  the air temperature. Surroundings that radiate at another temperature are not modelled.
- **Round runs only.** A duct or any bore that is not round in a zone is refused.
- **No ground, sky or condensation.** Every zone is air. A buried pipe, a clear-sky radiation loss and
  condensation on a cold pipe are outside the model.
- **Tall risers are flagged.** A vertical riser taller than about 6 m carries an out-of-range caution, because
  its outside film passes the stated range of its correlation. The range end is used and the run is named in
  the reply.
- **No delay or storage.** The fluid reaches the end of a run in the same step, and the pipe stores no heat over
  time.
- **No contact resistance** between layers.
- **Material data.** Built-in materials are representative values of each class and are marked as assumed in the
  reply. A material you state yourself is marked as your data.
- Two cases of one fluid and one wall material show two points of a model. They do not span it.

Results are for review by a professional engineer, who remains responsible. This comparison is not a design
certification.
