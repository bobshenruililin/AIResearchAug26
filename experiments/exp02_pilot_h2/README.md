# exp02_pilot_h2

Cheapest test of **H2 (isotonic overfit under shift)**.

Varies `n_cal` in {50,100,200,400} for logreg/rf on two binary-ish datasets.
Wine is excluded (multiclass + small n makes n_cal=400 infeasible).
