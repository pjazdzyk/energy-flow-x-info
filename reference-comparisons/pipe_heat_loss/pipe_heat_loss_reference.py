#!/usr/bin/env python3
"""Pipe heat loss to room or outdoor air, computed from first principles.

Standard library only. Run:  python3 pipe_heat_loss_reference.py

The script computes three cases and prints each beside the figure the EnergyFlowX
server returned for the same request, with the gap in percent. It then writes
expected_figures.json, the reference side of the comparison.

Method, in one pass per run (SI units, W, K, m):

  1. The stream cools along the run, so the run is taken at its mean stream temperature
     Tm = (Tin + Tout) / 2, and Tout comes from the exponential approach to the air:
         Tout = Ta + (Tin - Ta) * exp(-UA / (mdot * cp)).
     Tout and Tm are iterated until they agree.
  2. For a trial surface temperature Ts the heat flow per metre leaving the outer surface is
         q' = (h_conv + h_rad) * pi * Do * (Ts - Ta).
  3. The same q' is walked inward through each layer, each with its own conductivity taken at
     the mean of its two face temperatures:  dT = q' * ln(ro / ri) / (2 pi k).
  4. Through the inside film:  T_stream = T_inner_wall + q' / (h_in * pi * Di).
  5. Ts is found by a root search (bisection) so that step 4 returns Tm.
  UA = q' * L / (Tm - Ta).

Film coefficients (by name):
  inside        Gnielinski form, with the friction factor of the rough pipe from the Colebrook
                form, blended linearly in Re between laminar (Nu = 3.66) at Re 2300 and
                turbulent at Re 4000
  natural       Churchill and Chu form for a horizontal cylinder
  crossflow     Churchill and Bernstein form
  mixed         the natural and crossflow Nusselt numbers combined as (Nu_n^3 + Nu_f^3)^(1/3)
  radiation     grey surface in an enclosure at the air temperature:
                h_rad = emissivity * sigma * (Ts^2 + Ta^2) * (Ts + Ta)

Gaps are reported, not hidden. The server column is its answer to the request files in
requests/, recorded here with the mass flow its hydraulics found (the flow is an input of
this comparison, not a result under test).
"""
import json
import math
import os

SIGMA = 5.670374419e-8  # Stefan-Boltzmann constant, W/(m2 K4)
K0 = 273.15
G = 9.80665

# ---------------------------------------------------------------------------------------
# Fluid properties, with their basis
# ---------------------------------------------------------------------------------------

# Liquid water at 0.2 MPa: T [K], density [kg/m3], specific heat [J/(kg K)],
# conductivity [W/(m K)], dynamic viscosity [Pa s]. Basis: the IAPWS-95 formulation for
# density and specific heat, the IAPWS releases for viscosity and thermal conductivity,
# evaluated every 10 K and rounded to the digits shown. Linear interpolation between rows.
WATER = [
    (273.15, 999.89, 4219, 0.5557, 1791.5e-6),
    (283.15, 999.75, 4195, 0.5788, 1305.8e-6),
    (293.15, 998.25, 4184, 0.5981, 1001.6e-6),
    (303.15, 995.69, 4180, 0.6144, 797.2e-6),
    (313.15, 992.26, 4179, 0.6285, 652.7e-6),
    (323.15, 988.08, 4181, 0.6407, 546.5e-6),
    (333.15, 983.24, 4185, 0.6511, 466.1e-6),
    (343.15, 977.81, 4190, 0.6598, 403.6e-6),
    (353.15, 971.83, 4197, 0.6670, 354.1e-6),
    (363.15, 965.35, 4205, 0.6728, 314.2e-6),
    (373.15, 958.40, 4215, 0.6773, 281.6e-6),
]


def water(t):
    """rho, cp, k, mu, Pr of liquid water at t [K] by linear interpolation of WATER."""
    for lo, hi in zip(WATER, WATER[1:]):
        if lo[0] <= t <= hi[0]:
            f = (t - lo[0]) / (hi[0] - lo[0])
            rho, cp, k, mu = (lo[i] + f * (hi[i] - lo[i]) for i in range(1, 5))
            return rho, cp, k, mu, mu * cp / k
    raise ValueError("water table covers 273.15 K to 373.15 K, got %.2f K" % t)


def air(t, p=101325.0):
    """rho, cp, k, mu, Pr, nu of dry air at t [K] and p [Pa].

    Basis: ideal gas density (R = 287.05 J/(kg K)), constant cp = 1006 J/(kg K) over the
    range of these cases, and Sutherland's law for viscosity (mu0 = 1.716e-5 Pa s at
    273.15 K, S = 110.4 K) and conductivity (k0 = 0.0241 W/(m K) at 273.15 K, S = 194 K).
    """
    rho = p / (287.05 * t)
    cp = 1006.0
    mu = 1.716e-5 * (t / K0) ** 1.5 * (K0 + 110.4) / (t + 110.4)
    k = 0.0241 * (t / K0) ** 1.5 * (K0 + 194.0) / (t + 194.0)
    return rho, cp, k, mu, mu * cp / k, mu / rho


# ---------------------------------------------------------------------------------------
# Film coefficients
# ---------------------------------------------------------------------------------------

def friction_factor(re, rel_roughness):
    """Darcy friction factor of a rough round pipe: the implicit Colebrook form, by fixed-point iteration."""
    f = (0.79 * math.log(re) - 1.64) ** -2
    for _ in range(100):
        new = (-2.0 * math.log10(rel_roughness / 3.7 + 2.51 / (re * math.sqrt(f)))) ** -2
        if abs(new - f) < 1e-14:
            return new
        f = new
    return f


def inside_h(mdot, di, tm, roughness):
    """Inside film coefficient [W/(m2 K)] of water in a round pipe at mean temperature tm."""
    rho, cp, k, mu, pr = water(tm)
    re = 4.0 * mdot / (math.pi * di * mu)

    def turbulent(r):
        f = friction_factor(r, roughness / di)
        return (f / 8.0) * (r - 1000.0) * pr / (1.0 + 12.7 * math.sqrt(f / 8.0) * (pr ** (2.0 / 3.0) - 1.0))

    if re <= 2300.0:
        nu = 3.66
    elif re >= 4000.0:
        nu = turbulent(re)
    else:
        w = (re - 2300.0) / 1700.0
        nu = (1.0 - w) * 3.66 + w * turbulent(4000.0)
    return nu * k / di, re, pr


def outside_h(ts, ta, do, speed):
    """Convection coefficient [W/(m2 K)] on the outer surface of a horizontal cylinder."""
    tf = 0.5 * (ts + ta)
    rho, cp, k, mu, pr, nu = air(tf)
    beta = 1.0 / tf
    ra = G * beta * abs(ts - ta) * do ** 3 / (nu * (nu / pr))
    nu_n = (0.60 + 0.387 * ra ** (1.0 / 6.0) / (1.0 + (0.559 / pr) ** (9.0 / 16.0)) ** (8.0 / 27.0)) ** 2
    if speed > 0.0:
        re = speed * do / nu
        nu_f = 0.3 + (0.62 * math.sqrt(re) * pr ** (1.0 / 3.0)
                      / (1.0 + (0.4 / pr) ** (2.0 / 3.0)) ** 0.25
                      * (1.0 + (re / 282000.0) ** (5.0 / 8.0)) ** 0.8)
        nu_t = (nu_n ** 3 + nu_f ** 3) ** (1.0 / 3.0)
        regime = "FORCED" if nu_f > nu_n else "NATURAL"
    else:
        nu_t, regime = nu_n, "NATURAL"
    return nu_t * k / do, regime


def radiation_h(ts, ta, emissivity):
    return emissivity * SIGMA * (ts * ts + ta * ta) * (ts + ta)


# ---------------------------------------------------------------------------------------
# Layers
# ---------------------------------------------------------------------------------------

def conductivity(points, t):
    """Piecewise linear k(T) through points [(T_K, k)], held at the end values outside."""
    if t <= points[0][0]:
        return points[0][1]
    for (t0, k0), (t1, k1) in zip(points, points[1:]):
        if t <= t1:
            return k0 + (k1 - k0) * (t - t0) / (t1 - t0)
    return points[-1][1]


def layer_inner_face(t_outer, q_per_m, r_in, r_out, points):
    """Inner face temperature of a layer whose outer face is at t_outer, k at the mean of its faces."""
    t_in = t_outer
    for _ in range(100):
        k = conductivity(points, 0.5 * (t_in + t_outer))
        new = t_outer + q_per_m * math.log(r_out / r_in) / (2.0 * math.pi * k)
        if abs(new - t_in) < 1e-12:
            return new
        t_in = new
    return t_in


def stream_temperature_for(ts, ta, di, layers, emissivity, speed, h_in, tm_guess):
    """Heat flow per metre and the stream temperature that makes Ts the surface temperature."""
    r_out = di / 2.0 + sum(t for t, _ in layers)
    do = 2.0 * r_out
    h_c, regime = outside_h(ts, ta, do, speed)
    h_r = radiation_h(ts, ta, emissivity)
    q = (h_c + h_r) * math.pi * do * (ts - ta)
    t = ts
    r = r_out
    for thickness, points in reversed(layers):
        r_in = r - thickness
        t = layer_inner_face(t, q, r_in, r, points)
        r = r_in
    return t + q / (h_in * math.pi * di), q, h_c, h_r, regime, do


def solve_run(mdot, tin, ta, di, layers, emissivity, length, speed, roughness):
    """Loss, UA, outlet and the surface state of one run. layers run from the pipe wall outward:
    [(thickness [m], [(T_K, k W/(m K)), ...]), ...]."""
    tout = tin
    for _ in range(100):
        tm = 0.5 * (tin + tout)
        h_in, re, pr = inside_h(mdot, di, tm, roughness)
        lo, hi = ta + 1e-9, tm  # the surface lies between the air and the stream
        for _ in range(200):
            ts = 0.5 * (lo + hi)
            t_stream, q, h_c, h_r, regime, do = stream_temperature_for(
                ts, ta, di, layers, emissivity, speed, h_in, tm)
            if t_stream > tm:
                hi = ts
            else:
                lo = ts
            if hi - lo < 1e-11:
                break
        ua = q * length / (tm - ta)
        cp = water(tm)[1]
        new_out = ta + (tin - ta) * math.exp(-ua / (mdot * cp))
        if abs(new_out - tout) < 1e-10:
            tout = new_out
            break
        tout = new_out
    cp = water(0.5 * (tin + tout))[1]
    loss = mdot * cp * (tin - tout)
    return {"loss_W": loss, "per_m_W": loss / length, "ua_WpK": ua, "tout_K": tout, "tmean_K": 0.5 * (tin + tout),
            "ts_K": ts, "h_conv": h_c, "h_rad": h_r, "h_in": h_in, "reynolds": re, "regime": regime}


# ---------------------------------------------------------------------------------------
# Cases. Inputs below are the inputs of the REST requests in requests/.
# ---------------------------------------------------------------------------------------

# Steel pipe wall: conductivity 50 W/(m K) at 20 degC, emissivity 0.85 (the case's own material).
STEEL = [(K0 + 20.0, 50.0)]
# Mineral wool: conductivity points (the case's own material), emissivity 0.9.
WOOL = [(K0 + 20.0, 0.037), (K0 + 50.0, 0.042), (K0 + 100.0, 0.052)]
TIN = K0 + 70.0

# Server column: its answer to the request in requests/, copied from the reply.
# mdot is what the server's hydraulics found for the pressure difference of the request.
CASES = {
    "A_bare_steel_DN50": {
        "text": "bare steel DN50, 20 m, water 70 degC, still room air 20 degC",
        "mdot": 0.5317263914659468, "di": 0.0525, "length": 20.0, "ta": K0 + 20.0, "speed": 0.0, "roughness": 4.5e-5,
        "layers": [(0.0039, STEEL)], "emissivity": 0.85,
        "server": {"loss_W": 2308.2772711294497, "per_m_W": 115.41386355647248, "ua_WpK": 46.65080738581263,
                   "tout_K": 342.11339088792096, "ts_K": 342.22147357509436},
    },
    "B_wool_steel_DN50": {
        "text": "the same pipe with 40 mm of mineral wool, emissivity 0.9",
        "mdot": 0.5319617884256107, "di": 0.0525, "length": 20.0, "ta": K0 + 20.0, "speed": 0.0, "roughness": 4.5e-5,
        "layers": [(0.0039, STEEL), (0.040, WOOL)], "emissivity": 0.9,
        "server": {"loss_W": 284.20157024893444, "per_m_W": 14.210078512446723, "ua_WpK": 5.6912915900288175,
                   "tout_K": 343.0224863500457, "ts_K": 297.1660430041399},
    },
    "C_outdoor_DN25_cold": {
        "text": "bare steel DN25 outdoors, 40 m, 3 m/s wind, air -10 degC (the zone from 300 s)",
        "mdot": 0.11064904423275862, "di": 0.0266, "length": 40.0, "ta": K0 - 10.0, "speed": 3.0, "roughness": 4.5e-5,
        "layers": [(0.0032, STEEL)], "emissivity": 0.85,
        "server": {"loss_W": 10525.273156076953, "per_m_W": 263.1318289019238, "ua_WpK": 154.77875807541935,
                   "tout_K": 320.40672869837505, "ts_K": 329.66042409989615},
    },
    "C_outdoor_DN25_mild": {
        "text": "the same run, air 0 degC (the zone until 300 s)",
        "mdot": 0.11088047716755223, "di": 0.0266, "length": 40.0, "ta": K0, "speed": 3.0, "roughness": 4.5e-5,
        "layers": [(0.0032, STEEL)], "emissivity": 0.85,
        "server": {"loss_W": 9251.82026680918},
    },
}

# The scheduled run over 600 s in 60 s steps: air 0 degC for rows at 0 to 240 s, -10 degC from 300 s.
# Energy lost over the run, trapezoid over the rows (Wh). Server: the reply's energy for the run.
SCHEDULE_ROWS = [0, 60, 120, 180, 240, 300, 360, 420, 480, 540, 600]
SERVER_ENERGY_WH = 1658.7032027678417


def gap(ref, srv):
    return 100.0 * (srv / ref - 1.0)


def main():
    out = {"cases": {}}
    print("Pipe heat loss: reference (first principles) against the EnergyFlowX server")
    print("Gap = (server - reference) / reference, in percent.\n")
    results = {}
    for name, c in CASES.items():
        r = solve_run(c["mdot"], TIN, c["ta"], c["di"], c["layers"], c["emissivity"], c["length"], c["speed"], c["roughness"])
        results[name] = r
        print("%s: %s" % (name, c["text"]))
        rows = [("heat loss, W", "loss_W", 1.0, "%9.2f"), ("heat loss per metre, W/m", "per_m_W", 1.0, "%9.3f"),
                ("conductance UA, W/K", "ua_WpK", 1.0, "%9.3f"), ("outlet, degC", "tout_K", None, "%9.4f"),
                ("surface, degC", "ts_K", None, "%9.3f")]
        entry = {"input": {k: c[k] for k in ("mdot", "di", "length", "ta", "speed", "roughness", "emissivity")}, "figures": {}}
        for label, key, _, fmt in rows:
            if key not in c["server"]:
                continue
            ref, srv = r[key], c["server"][key]
            if key.endswith("_K"):
                print("   %-26s reference %s   server %s   difference %+.3f K" %
                      (label, fmt % (ref - K0), fmt % (srv - K0), srv - ref))
                entry["figures"][key] = {"reference": ref, "server": srv, "difference_K": srv - ref}
            else:
                print("   %-26s reference %s   server %s   gap %+.2f %%" % (label, fmt % ref, fmt % srv, gap(ref, srv)))
                entry["figures"][key] = {"reference": ref, "server": srv, "gap_percent": gap(ref, srv)}
        print("   films: inside %.0f, convection %.2f, radiation %.2f W/(m2 K), Re %.0f, outside regime %s\n" %
              (r["h_in"], r["h_conv"], r["h_rad"], r["reynolds"], r["regime"]))
        entry["films"] = {k: r[k] for k in ("h_in", "h_conv", "h_rad", "reynolds", "regime")}
        out["cases"][name] = entry

    # Scheduled outdoor run: each row against its air temperature, and the energy.
    cold, mild = results["C_outdoor_DN25_cold"]["loss_W"], results["C_outdoor_DN25_mild"]["loss_W"]
    rows_q = [mild if t < 300 else cold for t in SCHEDULE_ROWS]
    energy = 0.0
    for i, t in enumerate(SCHEDULE_ROWS):
        before = 0.0 if i == 0 else t - SCHEDULE_ROWS[i - 1]
        after = 0.0 if i == len(SCHEDULE_ROWS) - 1 else SCHEDULE_ROWS[i + 1] - t
        energy += rows_q[i] * 0.5 * (before + after)
    energy_wh = energy / 3600.0
    print("C_outdoor_DN25_scheduled: air 0 degC to 300 s, -10 degC from 300 s, 60 s steps to 600 s")
    print("   %-26s reference %9.2f   server %9.2f   gap %+.2f %%" % (
        "step 0 to 240 s, W", mild, CASES["C_outdoor_DN25_mild"]["server"]["loss_W"],
        gap(mild, CASES["C_outdoor_DN25_mild"]["server"]["loss_W"])))
    print("   %-26s reference %9.2f   server %9.2f   gap %+.2f %%" % (
        "step 300 to 600 s, W", cold, CASES["C_outdoor_DN25_cold"]["server"]["loss_W"],
        gap(cold, CASES["C_outdoor_DN25_cold"]["server"]["loss_W"])))
    print("   %-26s reference %9.2f   server %9.2f   gap %+.2f %%\n" % (
        "energy lost over 600 s, Wh", energy_wh, SERVER_ENERGY_WH, gap(energy_wh, SERVER_ENERGY_WH)))
    out["cases"]["C_outdoor_DN25_scheduled"] = {
        "rows_s": SCHEDULE_ROWS, "reference_loss_W": rows_q,
        "energy_Wh": {"reference": energy_wh, "server": SERVER_ENERGY_WH, "gap_percent": gap(energy_wh, SERVER_ENERGY_WH)},
    }

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expected_figures.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
        f.write("\n")
    print("wrote", path)


if __name__ == "__main__":
    main()
