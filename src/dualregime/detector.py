"""Two-channel regime detector: physics residual vs support density.

Channel 1 (perturbation): encoder–camera residual and denoise disagreement
(p(raw encoder) vs p(camera-projected encoder)). Optimistic encoder bias
keeps the observation *on* the training manifold, so PCA reconstruction
on encoder coordinates is the wrong signal.

Channel 2 (selection): camera-xy kNN / KS / domain-AUC. Residual stays
low because the pair is kept; only P(X) on the fixture changes.

Opposite routing: residual wins first (safety). Selection is never
labeled perturbation just because location moved.
"""

from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from scipy.stats import ks_2samp

from .density import fit_density_ratio_mv
from .world import CAM_IDX, CAM_XY_IDX, ENC_IDX, ENC_XY_IDX, project_encoder_to_camera

REGIME_IID = "iid"
REGIME_PERTURB = "perturb"
REGIME_SELECT = "select"


def physics_residual(X: np.ndarray) -> np.ndarray:
    X = np.asarray(X, dtype=np.float64)
    dxy = np.hypot(X[:, ENC_IDX[0]] - X[:, CAM_IDX[0]], X[:, ENC_IDX[1]] - X[:, CAM_IDX[1]])
    dth = np.abs(X[:, ENC_IDX[2]] - X[:, CAM_IDX[2]])
    return dxy + dth


class RegimeDetector:
    def __init__(
        self,
        resid_q: float = 0.95,
        knn_q: float = 0.95,
        denoise_q: float = 0.95,
        resid_mult: float = 1.5,
        knn_mult: float = 1.5,
        t_ks: float = 0.18,
        t_domain_auc: float = 0.62,
        knn_k: int = 10,
    ):
        self.resid_q = float(resid_q)
        self.knn_q = float(knn_q)
        self.denoise_q = float(denoise_q)
        self.resid_mult = float(resid_mult)
        self.knn_mult = float(knn_mult)
        self.t_ks = float(t_ks)
        self.t_domain_auc = float(t_domain_auc)
        self.knn_k = int(knn_k)
        self.resid_thresh: float = 0.0
        self.knn_thresh: float = 0.0
        self.denoise_thresh: float = 0.0
        self.t_abort: float = np.inf
        self._nn: NearestNeighbors | None = None
        self._pca_enc: PCA | None = None
        self._X_cal: np.ndarray | None = None
        self._cam_cal: np.ndarray | None = None
        self.median_pca_resid: float = 1.0
        self._p_fn = None

    def fit(self, X_iid: np.ndarray, p_fn=None) -> "RegimeDetector":
        """p_fn(X) -> (n,) success probabilities, optional, for denoise_l1."""
        X_iid = np.asarray(X_iid, dtype=np.float64)
        self._X_cal = X_iid
        self._cam_cal = X_iid[:, CAM_XY_IDX]
        r = physics_residual(X_iid)
        self.resid_thresh = float(np.quantile(r, self.resid_q) * self.resid_mult)
        self.t_abort = float(np.quantile(r, 0.99) * 3.0)
        k = min(self.knn_k, max(1, len(X_iid) - 1))
        self._nn = NearestNeighbors(n_neighbors=k, algorithm="auto").fit(self._cam_cal)
        knn = self.knn_cam(X_iid)
        self.knn_thresh = float(np.quantile(knn, self.knn_q) * self.knn_mult)
        enc = X_iid[:, ENC_XY_IDX]
        # 1-D PCA on 2-D encoder xy: a real reconstruction residual.
        # Optimistic bias sits near the mean, so this residual often *falls*.
        n_comp = 1
        self._pca_enc = PCA(n_components=n_comp, random_state=0).fit(enc)
        self.median_pca_resid = float(np.median(self.pca_resid(X_iid)) + 1e-8)
        self._p_fn = p_fn
        if p_fn is not None:
            d = self.denoise_l1(X_iid, p_fn)
            self.denoise_thresh = float(np.quantile(d, self.denoise_q) * 1.5)
        else:
            self.denoise_thresh = 0.15
        return self

    def knn_cam(self, X: np.ndarray) -> np.ndarray:
        assert self._nn is not None
        dist, _ = self._nn.kneighbors(np.asarray(X, dtype=np.float64)[:, CAM_XY_IDX])
        return dist.mean(axis=1)

    def pca_resid(self, X: np.ndarray) -> np.ndarray:
        """Encoder-xy PCA residual (diagnostic; not the perturbation router)."""
        assert self._pca_enc is not None
        enc = np.asarray(X, dtype=np.float64)[:, ENC_XY_IDX]
        hat = self._pca_enc.inverse_transform(self._pca_enc.transform(enc))
        return np.linalg.norm(enc - hat, axis=1)

    def denoise_l1(self, X: np.ndarray, p_fn) -> np.ndarray:
        p_raw = np.asarray(p_fn(X), dtype=np.float64).reshape(-1)
        p_hat = np.asarray(p_fn(project_encoder_to_camera(X)), dtype=np.float64).reshape(-1)
        return np.abs(p_raw - p_hat)

    def batch_ks_max(self, X: np.ndarray) -> float:
        assert self._X_cal is not None
        X = np.asarray(X, dtype=np.float64)
        stats = []
        for j in list(CAM_XY_IDX) + [CAM_IDX[2]]:
            stats.append(ks_2samp(self._X_cal[:, j], X[:, j]).statistic)
        return float(np.max(stats))

    def predict(
        self,
        X: np.ndarray,
        p_fn=None,
        use_batch: bool = True,
    ) -> np.ndarray:
        X = np.asarray(X, dtype=np.float64)
        n = len(X)
        r = physics_residual(X)
        knn = self.knn_cam(X)
        p_fn = p_fn if p_fn is not None else self._p_fn
        d1 = self.denoise_l1(X, p_fn) if p_fn is not None else np.zeros(n)
        out = np.full(n, REGIME_IID, dtype=object)
        # Physics residual is the perturbation channel. Denoise disagreement
        # is a helper, not a substitute: optimistic encoder can look in-support.
        perturb = r > self.resid_thresh
        if p_fn is not None:
            perturb = perturb | ((d1 > self.denoise_thresh) & (r > 0.5 * self.resid_thresh))
        select = (~perturb) & (knn > self.knn_thresh)
        if use_batch and n >= 16 and self._X_cal is not None:
            ks = self.batch_ks_max(X)
            dr = fit_density_ratio_mv(self._X_cal, X, seed=0)
            # Require a real P(X) change (AUC), not a fluky KS on i.i.d. noise.
            batch_select = (dr.domain_auc > self.t_domain_auc) or (
                ks > self.t_ks and dr.domain_auc > 0.55
            )
            if batch_select:
                select = (~perturb) & np.ones(n, dtype=bool)
            frac_high_resid = float((r > self.resid_thresh).mean())
            if frac_high_resid > 0.20 and (p_fn is None or float(d1.mean()) > 0.5 * self.denoise_thresh):
                perturb = np.ones(n, dtype=bool)
                select = np.zeros(n, dtype=bool)
        out[perturb] = REGIME_PERTURB
        out[select] = REGIME_SELECT
        return out

    def predict_stream(self, X: np.ndarray, p_fn=None, window: int = 32, stride: int = 8) -> np.ndarray:
        """Point residual + rolling unlabeled window. Do not batch the whole stream."""
        X = np.asarray(X, dtype=np.float64)
        n = len(X)
        p_fn = p_fn if p_fn is not None else self._p_fn
        # Pointwise first (no global batch override).
        out = self.predict(X, p_fn=p_fn, use_batch=False)
        r = physics_residual(X)
        d1 = self.denoise_l1(X, p_fn) if p_fn is not None else np.zeros(n)
        for t0 in range(0, n, stride):
            t1 = min(n, t0 + stride)
            lo = max(0, t1 - window)
            batch = X[lo:t1]
            if len(batch) < 16:
                continue
            ks = self.batch_ks_max(batch)
            dr = fit_density_ratio_mv(self._X_cal, batch, seed=0)
            frac_high = float((r[lo:t1] > self.resid_thresh).mean())
            den_mean = float(d1[lo:t1].mean()) if p_fn is not None else 0.0
            batch_pert = frac_high > 0.20 and (p_fn is None or den_mean > 0.5 * self.denoise_thresh)
            batch_sel = (dr.domain_auc > self.t_domain_auc) or (
                ks > self.t_ks and dr.domain_auc > 0.55
            )
            for i in range(t0, t1):
                if batch_pert or out[i] == REGIME_PERTURB:
                    out[i] = REGIME_PERTURB
                elif batch_sel and out[i] != REGIME_PERTURB:
                    out[i] = REGIME_SELECT
        return out
