# exp09: planar peg-in-hole insert vs abort

Kinematic cartoon (not a robot). Optimistic encoder scale 0.4 vs
right-half fixture selection (`x >= 0`). Headline stack: physics
residual → project encoder onto camera then source T; density-ratio
channel → weighted LAC, defer not abort.

Modes: `router`, `detector_off`, `always_abort`, `illegal_T`,
`denoise_off`, `always_project`, `oracle`.

JSON: `results/exp09_peg_insert.json`. Do not hand-edit.
