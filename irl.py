"""Maximum-entropy inverse reinforcement learning for scientists' topic choices.

The model
---------
State  s : (citation tier of current topic, time in topic, career stage), 3 x 3 x 3 = 27 states
Action a : 0 = stay in the same topic, 1 = move to a nearby topic (same subfield),
           2 = jump to a distant topic (different subfield)
Reward   : r(s, a) = theta_cite * tier(s) + theta_near * [a = near] + theta_far * [a = far]
           tier(s) is 0, 0.5 or 1. Staying is the baseline (no action reward).

Scientists choose "softly optimally":
    Q(s, a) = r(s, a) + gamma * sum_s' P(s' | s, a) V(s')
    V(s)    = log sum_a exp Q(s, a)
    pi(a|s) = exp(Q(s, a) - V(s))

The weights theta maximise the log-likelihood of the observed choices. This is
maximum causal entropy IRL, the same estimator as Rust's nested fixed-point logit.
"""
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp

N_TIER, N_TENURE, N_CAREER = 3, 3, 3
N_STATES = N_TIER * N_TENURE * N_CAREER
N_ACTIONS = 3
ACTIONS = ("stay", "near", "far")
PARAMS = ("theta_cite", "theta_near", "theta_far")


def state_index(tier, tenure, career):
    """Map the three state parts (each 0, 1 or 2) to one index 0..26."""
    return (np.asarray(tier) * N_TENURE + np.asarray(tenure)) * N_CAREER + np.asarray(career)


def state_parts():
    """Return arrays (tier, tenure, career) for states 0..26."""
    return np.unravel_index(np.arange(N_STATES), (N_TIER, N_TENURE, N_CAREER))


def build_features():
    """Feature array phi[s, a, k] so that reward = phi @ theta."""
    tier, _, _ = state_parts()
    phi = np.zeros((N_STATES, N_ACTIONS, len(PARAMS)))
    phi[:, :, 0] = (tier / (N_TIER - 1))[:, None]   # citation tier, same for every action
    phi[:, 1, 1] = 1.0                              # nearby move
    phi[:, 2, 2] = 1.0                              # distant jump
    return phi


PHI = build_features()


def count_arrays(s, a, s_next, weights=None):
    """Count observed choices (S x A) and transitions (S x A x S')."""
    idx = (np.asarray(s) * N_ACTIONS + np.asarray(a)) * N_STATES + np.asarray(s_next)
    trans = np.bincount(idx, weights=weights, minlength=N_STATES * N_ACTIONS * N_STATES)
    trans = trans.reshape(N_STATES, N_ACTIONS, N_STATES).astype(float)
    return trans.sum(axis=2), trans


def transition_probs(trans_counts, alpha=1.0):
    """Estimate P(s' | s, a) from counts, smoothed towards a pooled estimate.

    The pooled estimate ignores the current citation tier (same time-in-topic,
    career stage and action), and falls back to the action's overall pattern.
    Rare (s, a) pairs therefore borrow strength without impossible jumps.
    """
    T = trans_counts.reshape(N_TIER, N_TENURE, N_CAREER, N_ACTIONS, N_STATES)
    pooled = T.sum(axis=0, keepdims=True)
    pooled_n = pooled.sum(axis=-1, keepdims=True)

    marginal = trans_counts.sum(axis=0)                        # (A, S')
    marginal_n = marginal.sum(axis=-1, keepdims=True)
    marginal_p = np.where(marginal_n > 0, marginal / np.maximum(marginal_n, 1e-12), 1.0 / N_STATES)

    prior = np.where(pooled_n > 0, pooled / np.maximum(pooled_n, 1e-12),
                     np.broadcast_to(marginal_p, pooled.shape))
    prior = np.broadcast_to(prior, T.shape).reshape(N_STATES, N_ACTIONS, N_STATES)

    n_sa = trans_counts.sum(axis=2, keepdims=True)
    return (trans_counts + alpha * prior) / (n_sa + alpha)


def soft_q(theta, P, gamma, phi=PHI, tol=1e-10, max_iter=200, V0=None):
    """Solve the soft Bellman equation. Returns Q (S x A) and V (S).

    Uses soft policy iteration: take the softmax policy of the current Q, then
    solve exactly for that policy's value (a 27 x 27 linear system), and repeat.
    It reaches the same fixed point as value iteration in a few steps.
    V0 is an optional starting guess; it changes speed, not the answer.
    """
    r = phi @ theta
    V = np.zeros(N_STATES) if V0 is None else V0.copy()
    eye = np.eye(N_STATES)
    for _ in range(max_iter):
        Q = r + gamma * (P @ V)
        V_new = logsumexp(Q, axis=1)
        if np.max(np.abs(V_new - V)) < tol:
            V = V_new
            break
        logpi = Q - V_new[:, None]
        pi = np.exp(logpi)
        Pi_P = np.einsum("sa,sat->st", pi, P)
        V = np.linalg.solve(eye - gamma * Pi_P, (pi * (r - logpi)).sum(axis=1))
    Q = r + gamma * (P @ V)
    return Q, logsumexp(Q, axis=1)


def policy(theta, P, gamma, phi=PHI):
    """Choice probabilities pi(a | s) implied by theta."""
    Q, V = soft_q(theta, P, gamma, phi)
    return np.exp(Q - V[:, None])


def loglik_and_grad(theta, choices, P, gamma, phi=PHI, cache=None):
    """Log-likelihood of the observed choices and its exact gradient.

    `cache` (a dict) carries the last value function between calls as a warm start.
    """
    V0 = None if cache is None else cache.get("V")
    Q, V = soft_q(theta, P, gamma, phi, V0=V0)
    if cache is not None:
        cache["V"] = V
    logpi = Q - V[:, None]
    pi = np.exp(logpi)
    ll = float((choices * logpi).sum())

    # dV/dtheta solves (I - gamma * Pi P) dV = Pi phi, where Pi averages over pi(a|s)
    Pi_P = np.einsum("sa,sat->st", pi, P)
    Pi_phi = np.einsum("sa,sak->sk", pi, phi)
    dV = np.linalg.solve(np.eye(N_STATES) - gamma * Pi_P, Pi_phi)
    dQ = phi + gamma * np.einsum("sat,tk->sak", P, dV)
    grad = np.einsum("sa,sak->k", choices, dQ - dV[:, None, :])
    return ll, grad


def fit(choices, P, gamma, phi=PHI, theta0=None):
    """Find the reward weights that best explain the observed choices."""
    if theta0 is None:
        theta0 = np.zeros(phi.shape[2])

    cache = {}

    def objective(theta):
        ll, grad = loglik_and_grad(theta, choices, P, gamma, phi, cache)
        return -ll, -grad

    res = minimize(objective, theta0, jac=True, method="L-BFGS-B",
                   options={"maxiter": 500, "gtol": 1e-7})
    return {"theta": res.x, "loglik": -res.fun, "n": float(choices.sum()),
            "converged": bool(res.success)}


def fit_counts(choices, trans_counts, gamma, theta0=None):
    """Estimate transitions from counts, then fit theta."""
    P = transition_probs(trans_counts)
    return fit(choices, P, gamma, theta0=theta0)
