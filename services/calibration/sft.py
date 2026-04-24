"""Supervised fine-tuning loop for calibration temperature scaling. © 2026 AXIOLEV Holdings LLC

Minimises Brier loss over temperature T via gradient descent.
Pure-numpy by default; uses torch when available and requested.
"""
from __future__ import annotations

from typing import Iterator, Optional

import numpy as np

try:
    import torch
    import torch.nn.functional as F
    _TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover
    _TORCH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Numpy helpers
# ---------------------------------------------------------------------------

def _sigmoid(z: np.ndarray, T: float) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z / T, -30, 30)))


def _softmax(z: np.ndarray, T: float) -> np.ndarray:
    z_s = z / T
    z_s = z_s - z_s.max(axis=-1, keepdims=True)
    e = np.exp(z_s)
    return e / e.sum(axis=-1, keepdims=True)


def _brier_and_grad_np(
    logits: np.ndarray,
    labels: np.ndarray,
    mask: Optional[np.ndarray],
    T: float,
) -> tuple[float, float]:
    """Return (brier_loss, dL/dT) using the analytical gradient."""
    if logits.ndim == 1:
        p = _sigmoid(logits, T)
        residual = p - labels.astype(float)
        # dp/dT = -(z/T^2) * p * (1 - p)
        dp_dT = -(logits / (T * T)) * p * (1.0 - p)
        loss_per = residual ** 2
        grad_per = 2.0 * residual * dp_dT
    else:
        p = _softmax(logits, T)
        n, _ = p.shape
        y_oh = np.zeros_like(p)
        y_oh[np.arange(n), labels] = 1.0
        residual = p - y_oh
        loss_per = (residual ** 2).sum(axis=1)
        # dp_j/dT = -p_j / T^2 * (z_j - E_p[z])
        z_mean = (p * logits).sum(axis=1, keepdims=True)  # (N,1)
        dp_dT = -p / (T * T) * (logits - z_mean)          # (N,C)
        grad_per = (2.0 * residual * dp_dT).sum(axis=1)    # (N,)

    if mask is not None:
        m = np.asarray(mask, dtype=bool)
        loss_per = loss_per[m]
        grad_per = grad_per[m]

    if len(loss_per) == 0:
        return 0.0, 0.0
    return float(loss_per.mean()), float(grad_per.mean())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def sft_temperature_loop(
    logits: np.ndarray,
    labels: np.ndarray,
    mask: Optional[np.ndarray] = None,
    n_epochs: int = 100,
    lr: float = 0.3,
    init_T: float = 2.0,
    tol: float = 1e-5,
    use_torch: bool = True,
) -> Iterator[float]:
    """Supervised fine-tuning loop that yields calibration temperature T each epoch.

    Minimises mean Brier loss over (logits, labels, mask) w.r.t. a scalar
    temperature T applied before sigmoid/softmax:

        p = sigmoid(logits / T)          # binary  (logits.ndim == 1)
        p = softmax(logits / T, dim=-1)  # multiclass

    Args:
        logits:    (N,) binary logits or (N, C) multiclass logits.
        labels:    (N,) integer class labels.
        mask:      (N,) boolean; True = include in loss. None = all.
        n_epochs:  Number of gradient steps.
        lr:        Learning rate for gradient descent on T.
        init_T:    Initial temperature (>1 = under-confident; <1 = over-confident).
        tol:       Early-stop when |ΔT| < tol for two consecutive steps.
        use_torch: Prefer torch autograd when available.

    Yields:
        T (float) after each epoch.
    """
    logits = np.asarray(logits, dtype=float)
    labels = np.asarray(labels, dtype=int)
    if mask is not None:
        mask = np.asarray(mask, dtype=bool)

    if use_torch and _TORCH_AVAILABLE:
        yield from _loop_torch(logits, labels, mask, n_epochs, lr, init_T, tol)
    else:
        yield from _loop_numpy(logits, labels, mask, n_epochs, lr, init_T, tol)


def _loop_numpy(
    logits: np.ndarray,
    labels: np.ndarray,
    mask: Optional[np.ndarray],
    n_epochs: int,
    lr: float,
    init_T: float,
    tol: float,
) -> Iterator[float]:
    T = float(init_T)
    prev_T = T
    converged = False

    # Adam-style adaptive lr
    m = 0.0   # first moment
    v = 0.0   # second moment
    beta1, beta2, eps_adam = 0.9, 0.999, 1e-8

    for epoch in range(1, n_epochs + 1):
        if not converged:
            _, grad = _brier_and_grad_np(logits, labels, mask, T)
            m = beta1 * m + (1 - beta1) * grad
            v = beta2 * v + (1 - beta2) * grad * grad
            m_hat = m / (1 - beta1 ** epoch)
            v_hat = v / (1 - beta2 ** epoch)
            T -= lr * m_hat / (v_hat ** 0.5 + eps_adam)
            T = float(np.clip(T, 1e-3, 100.0))
            if abs(T - prev_T) < tol and epoch > 5:
                converged = True
            prev_T = T
        yield T


def _loop_torch(
    logits: np.ndarray,
    labels: np.ndarray,
    mask: Optional[np.ndarray],
    n_epochs: int,
    lr: float,
    init_T: float,
    tol: float,
) -> Iterator[float]:  # pragma: no cover — torch path
    import torch
    import torch.nn.functional as F

    t_logits = torch.tensor(logits, dtype=torch.float32)
    t_labels = torch.tensor(labels, dtype=torch.long)
    t_mask = torch.tensor(mask, dtype=torch.bool) if mask is not None else None

    T = torch.nn.Parameter(torch.tensor([float(init_T)]))
    opt = torch.optim.Adam([T], lr=lr)
    prev_T = init_T

    for epoch in range(n_epochs):
        opt.zero_grad()
        T_clamped = T.clamp(min=1e-3, max=100.0)

        if t_logits.ndim == 1:
            p = torch.sigmoid(t_logits / T_clamped)
            y_f = t_labels.float()
            loss_per = (p - y_f) ** 2
        else:
            p = F.softmax(t_logits / T_clamped, dim=-1)
            y_oh = F.one_hot(t_labels, num_classes=p.shape[-1]).float()
            loss_per = ((p - y_oh) ** 2).sum(dim=-1)

        loss = loss_per[t_mask].mean() if t_mask is not None else loss_per.mean()
        loss.backward()
        opt.step()

        with torch.no_grad():
            T.clamp_(min=1e-3, max=100.0)

        t_val = float(T.item())
        if abs(t_val - prev_T) < tol and epoch > 5:
            for _ in range(epoch + 1, n_epochs):
                yield t_val
            return
        prev_T = t_val
        yield t_val
