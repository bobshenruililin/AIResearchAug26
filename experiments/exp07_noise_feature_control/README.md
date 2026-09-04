# exp07_noise_feature_control

Control: shift the *last* 4 features instead of the first 4. On
`synthetic_shift`, early features are more label-correlated (feature 0 is
constructed that way). If calibration breaks equally here, the H1 story is
“any mean shift,” not “shift of predictive covariates.”
