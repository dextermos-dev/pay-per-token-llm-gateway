import { Injectable } from '@nestjs/common';
import { logger } from '@x402/logger';
import type { ProviderRouteCandidate } from '../routes/routes.service';

/**
 * How a request is chosen when one model is served by several providers.
 *
 * - `round-robin` — smooth weighted round-robin. Providers take turns in
 *   proportion to their configured weight, so weights of 70/30 produce a 7:3
 *   split that is spread evenly rather than delivered in bursts.
 * - `least-latency` — the provider with the lowest observed average latency.
 *   Providers that have not been measured yet go first, once, so a new one is
 *   sampled instead of being starved by reputation it has not earned.
 */
export type BalancingStrategy = 'round-robin' | 'least-latency';

/** Consecutive failures that take a provider out of rotation. */
export const FAILURES_BEFORE_OPEN = 3;

/** How long a provider stays out before it is tried again. */
export const CIRCUIT_COOLDOWN_MS = 30_000;

export interface ProviderHealth {
  providerId: string;
  requests: number;
  failures: number;
  averageLatencyMs: number | null;
  consecutiveFailures: number;
  /** True while the provider is being skipped. */
  circuitOpen: boolean;
  /** ISO timestamp the circuit opened, or null. */
  circuitOpenedAt: string | null;
}

interface HealthState {
  requests: number;
  failures: number;
  totalLatencyMs: number;
  measured: number;
  consecutiveFailures: number;
  circuitOpenedAt: number | null;
}

function emptyState(): HealthState {
  return {
    requests: 0,
    failures: 0,
    totalLatencyMs: 0,
    measured: 0,
    consecutiveFailures: 0,
    circuitOpenedAt: null,
  };
}

/**
 * Choose between the providers that can serve a model, and remember how each
 * one behaved.
 *
 * State is kept **per model**, not per request path. The same model can be
 * reached by more than one path, and selection happens with the request's path in
 * hand while the result is recorded with the stored route's — keying on the path
 * would file those two facts in different buckets, and the health this keeps
 * would never see the traffic it is supposed to be judging.
 *
 * The state is in-process on purpose. It is a routing decision, not a record of
 * payment: it can be lost and rebuilt from observed traffic, and putting it in
 * the database would mean writing a row about a provider that may never be paid.
 * What must not be lost — what was charged, to whom — is the ledger, and this
 * does not touch it.
 *
 * With more than one gateway instance, each balances independently. That is said
 * here rather than implied: a deployment that wants one global split needs shared
 * state, and pretending otherwise would be a worse bug than the one this fixes.
 */
@Injectable()
export class LoadBalancerService {
  private readonly health = new Map<string, Map<string, HealthState>>();
  /** Smooth weighted round-robin keeps one running current weight per provider. */
  private readonly runningWeight = new Map<string, Map<string, number>>();

  private stateFor(model: string, providerId: string): HealthState {
    let byProvider = this.health.get(model);
    if (!byProvider) {
      byProvider = new Map<string, HealthState>();
      this.health.set(model, byProvider);
    }
    const existing = byProvider.get(providerId);
    if (existing) return existing;
    const fresh = emptyState();
    byProvider.set(providerId, fresh);
    return fresh;
  }

  /**
   * Whether a provider may be tried right now.
   *
   * A circuit opens after `FAILURES_BEFORE_OPEN` consecutive failures and stays
   * open for `CIRCUIT_COOLDOWN_MS`. After the cooldown it is eligible again —
   * half-open, in the usual vocabulary — and the next success closes it, while
   * the next failure opens it again immediately because the consecutive count was
   * never cleared.
   */
  isAvailable(model: string, providerId: string, now: number = Date.now()): boolean {
    const state = this.stateFor(model, providerId);
    if (state.circuitOpenedAt === null) return true;
    return now - state.circuitOpenedAt >= CIRCUIT_COOLDOWN_MS;
  }

  /**
   * Pick one candidate, or null when every one of them is out.
   *
   * Null is a real answer, not a fallback to an open circuit: sending traffic to
   * a provider that has just failed three times in a row turns a degraded
   * deployment into a broken one.
   */
  selectRoute(
    model: string,
    candidates: readonly ProviderRouteCandidate[],
    strategy: BalancingStrategy = 'round-robin',
    now: number = Date.now(),
  ): ProviderRouteCandidate | null {
    if (candidates.length === 0) return null;

    const available = candidates.filter((c) => this.isAvailable(model, c.providerId, now));
    if (available.length === 0) {
      logger.warn('Every provider is circuit-open', { model });
      return null;
    }

    return strategy === 'least-latency'
      ? this.pickLeastLatency(model, available)
      : this.pickWeighted(model, available);
  }

  /** Smooth weighted round-robin: raise every weight, take the highest, lower it. */
  private pickWeighted(
    model: string,
    candidates: readonly ProviderRouteCandidate[],
  ): ProviderRouteCandidate {
    const total = candidates.reduce((sum, c) => sum + c.weight, 0);

    let running = this.runningWeight.get(model);
    if (!running) {
      running = new Map<string, number>();
      this.runningWeight.set(model, running);
    }

    let chosen: ProviderRouteCandidate | null = null;
    let best = Number.NEGATIVE_INFINITY;
    for (const candidate of candidates) {
      const raised = (running.get(candidate.providerId) ?? 0) + candidate.weight;
      running.set(candidate.providerId, raised);
      if (raised > best) {
        best = raised;
        chosen = candidate;
      }
    }

    if (chosen === null) return candidates[0] as ProviderRouteCandidate;
    running.set(chosen.providerId, best - total);
    return chosen;
  }

  /** Lowest measured average, and anything unmeasured before that, once. */
  private pickLeastLatency(
    model: string,
    candidates: readonly ProviderRouteCandidate[],
  ): ProviderRouteCandidate {
    const unmeasured = candidates.find(
      (c) => this.stateFor(model, c.providerId).measured === 0,
    );
    if (unmeasured) return unmeasured;

    let chosen = candidates[0] as ProviderRouteCandidate;
    let best = Number.POSITIVE_INFINITY;
    for (const candidate of candidates) {
      const state = this.stateFor(model, candidate.providerId);
      const average = state.totalLatencyMs / Math.max(1, state.measured);
      if (average < best) {
        best = average;
        chosen = candidate;
      }
    }
    return chosen;
  }

  /**
   * Record what happened on a request. Called after the upstream answers, and
   * with `ok: false` for a timeout or a failing upstream.
   */
  record(
    model: string,
    providerId: string,
    outcome: { ok: boolean; latencyMs?: number },
  ): void {
    const state = this.stateFor(model, providerId);
    state.requests += 1;

    if (typeof outcome.latencyMs === 'number' && Number.isFinite(outcome.latencyMs)) {
      state.totalLatencyMs += outcome.latencyMs;
      state.measured += 1;
    }

    if (outcome.ok) {
      state.consecutiveFailures = 0;
      if (state.circuitOpenedAt !== null) {
        logger.info('Provider circuit closed', { providerId, model });
        state.circuitOpenedAt = null;
      }
      return;
    }

    state.failures += 1;
    state.consecutiveFailures += 1;
    if (
      state.consecutiveFailures >= FAILURES_BEFORE_OPEN &&
      state.circuitOpenedAt === null
    ) {
      state.circuitOpenedAt = Date.now();
      logger.warn('Provider circuit opened', {
        providerId,
        model,
        consecutiveFailures: state.consecutiveFailures,
      });
    }
  }

  /** Per-provider health for one model, or for every model seen so far. */
  status(model?: string): ProviderHealth[] {
    const models = model === undefined ? [...this.health.keys()] : [model];
    const now = Date.now();
    const rows: ProviderHealth[] = [];

    for (const each of models) {
      const byProvider = this.health.get(each);
      if (!byProvider) continue;
      for (const [providerId, state] of byProvider) {
        rows.push({
          providerId,
          requests: state.requests,
          failures: state.failures,
          averageLatencyMs: state.measured === 0
            ? null
            : Math.round(state.totalLatencyMs / state.measured),
          consecutiveFailures: state.consecutiveFailures,
          circuitOpen: !this.isAvailable(each, providerId, now),
          circuitOpenedAt: state.circuitOpenedAt === null
            ? null
            : new Date(state.circuitOpenedAt).toISOString(),
        });
      }
    }
    return rows;
  }

  /** Drop all state. For a deployment that wants a clean slate, and for tests. */
  reset(): void {
    this.health.clear();
    this.runningWeight.clear();
  }
}
