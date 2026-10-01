import { Test, TestingModule } from '@nestjs/testing';
import {
  CIRCUIT_COOLDOWN_MS,
  FAILURES_BEFORE_OPEN,
  LoadBalancerService,
} from './load-balancer.service';
import type { ProviderRouteCandidate } from '../routes/routes.service';
import type { RouteConfig } from '@x402/types';

function makeRoute(overrides: Partial<RouteConfig> = {}): RouteConfig {
  return {
    id: 'route-1',
    providerId: 'provider-1',
    path: '/v1/chat/completions',
    upstreamUrl: 'https://api.openai.com/v1/chat/completions',
    model: 'gpt-4',
    pricingModel: 'flat',
    flatPrice: '1000000',
    acceptedAssets: ['USDC'],
    rateLimit: 10,
    active: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    ...overrides,
  };
}

function candidate(providerId: string, weight = 1): ProviderRouteCandidate {
  return {
    route: makeRoute({ id: `route-${providerId}`, providerId }),
    providerId,
    weight,
  };
}

const MODEL = 'gpt-4';

describe('LoadBalancerService', () => {
  let service: LoadBalancerService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [LoadBalancerService],
    }).compile();

    service = module.get<LoadBalancerService>(LoadBalancerService);
  });

  describe('choosing between providers', () => {
    it('returns null when there is nothing to choose from', () => {
      expect(service.selectRoute(MODEL, [])).toBeNull();
    });

    it('serves a single provider every time', () => {
      const only = candidate('provider-a');
      for (let i = 0; i < 5; i += 1) {
        expect(service.selectRoute(MODEL, [only])?.providerId).toBe('provider-a');
      }
    });

    it('takes turns between equal providers', () => {
      const candidates = [candidate('provider-a'), candidate('provider-b')];

      const picked = Array.from({ length: 6 }, () =>
        service.selectRoute(MODEL, candidates)?.providerId,
      );

      expect(picked).toEqual([
        'provider-a',
        'provider-b',
        'provider-a',
        'provider-b',
        'provider-a',
        'provider-b',
      ]);
    });

    it('splits traffic in proportion to configured weight', () => {
      const candidates = [candidate('provider-a', 70), candidate('provider-b', 30)];

      const counts: Record<string, number> = {};
      for (let i = 0; i < 100; i += 1) {
        const chosen = service.selectRoute(MODEL, candidates)?.providerId;
        if (chosen) counts[chosen] = (counts[chosen] ?? 0) + 1;
      }

      // Exactly 70/30 over a full cycle, not approximately: smooth weighted
      // round-robin is deterministic, which is what makes it testable.
      expect(counts['provider-a']).toBe(70);
      expect(counts['provider-b']).toBe(30);
    });

    it('spreads a weighted split evenly rather than in bursts', () => {
      const candidates = [candidate('provider-a', 70), candidate('provider-b', 30)];

      const picked = Array.from({ length: 10 }, () =>
        service.selectRoute(MODEL, candidates)?.providerId,
      );

      // A burst implementation would give seven A's then three B's.
      expect(picked.filter((p) => p === 'provider-b')).toHaveLength(3);
      expect(picked.indexOf('provider-b')).toBeLessThan(4);
      expect(picked.lastIndexOf('provider-b')).toBeGreaterThan(5);
    });

    it('keeps a separate rotation per model', () => {
      const candidates = [candidate('provider-a'), candidate('provider-b')];

      const first = service.selectRoute('gpt-4', candidates)?.providerId;
      const other = service.selectRoute('claude-3', candidates)?.providerId;
      const second = service.selectRoute('gpt-4', candidates)?.providerId;

      expect(first).toBe('provider-a');
      expect(other).toBe('provider-a');
      expect(second).toBe('provider-b');
    });
  });

  describe('least latency', () => {
    it('prefers the provider that has been answering faster', () => {
      const candidates = [candidate('slow'), candidate('fast')];
      service.record(MODEL, 'slow', { ok: true, latencyMs: 900 });
      service.record(MODEL, 'fast', { ok: true, latencyMs: 120 });

      for (let i = 0; i < 4; i += 1) {
        expect(service.selectRoute(MODEL, candidates, 'least-latency')?.providerId)
          .toBe('fast');
      }
    });

    it('samples a provider it has never measured instead of starving it', () => {
      const candidates = [candidate('measured'), candidate('brand-new')];
      service.record(MODEL, 'measured', { ok: true, latencyMs: 10 });

      expect(service.selectRoute(MODEL, candidates, 'least-latency')?.providerId)
        .toBe('brand-new');
    });

    it('falls back to the measured ones once everything has been sampled', () => {
      const candidates = [candidate('slow'), candidate('fast')];
      service.record(MODEL, 'slow', { ok: true, latencyMs: 900 });
      service.record(MODEL, 'fast', { ok: true, latencyMs: 120 });

      expect(service.selectRoute(MODEL, candidates, 'least-latency')?.providerId)
        .toBe('fast');
    });
  });

  describe('circuit breaker', () => {
    it('keeps serving a provider that fails, up to the threshold', () => {
      const candidates = [candidate('flaky'), candidate('steady')];

      service.record(MODEL, 'flaky', { ok: false });
      service.record(MODEL, 'flaky', { ok: false });

      const picked = Array.from({ length: 4 }, () =>
        service.selectRoute(MODEL, candidates)?.providerId,
      );
      expect(picked).toContain('flaky');
    });

    it('stops choosing a provider after consecutive failures', () => {
      const candidates = [candidate('flaky'), candidate('steady')];

      for (let i = 0; i < FAILURES_BEFORE_OPEN; i += 1) {
        service.record(MODEL, 'flaky', { ok: false });
      }

      const picked = Array.from({ length: 6 }, () =>
        service.selectRoute(MODEL, candidates)?.providerId,
      );
      expect(picked.every((p) => p === 'steady')).toBe(true);
    });

    it('returns null rather than sending traffic to an open circuit', () => {
      const candidates = [candidate('only-provider')];
      for (let i = 0; i < FAILURES_BEFORE_OPEN; i += 1) {
        service.record(MODEL, 'only-provider', { ok: false });
      }

      expect(service.selectRoute(MODEL, candidates)).toBeNull();
    });

    it('closes the circuit when the provider answers again', () => {
      const candidates = [candidate('flaky'), candidate('steady')];
      for (let i = 0; i < FAILURES_BEFORE_OPEN; i += 1) {
        service.record(MODEL, 'flaky', { ok: false });
      }
      expect(service.isAvailable(MODEL, 'flaky')).toBe(false);

      service.record(MODEL, 'flaky', { ok: true });

      expect(service.isAvailable(MODEL, 'flaky')).toBe(true);
      const picked = Array.from({ length: 4 }, () =>
        service.selectRoute(MODEL, candidates)?.providerId,
      );
      expect(picked).toContain('flaky');
    });

    it('tries an open provider again after the cooldown', () => {
      const candidates = [candidate('flaky'), candidate('steady')];
      for (let i = 0; i < FAILURES_BEFORE_OPEN; i += 1) {
        service.record(MODEL, 'flaky', { ok: false });
      }

      const before = Date.now();
      expect(service.selectRoute(MODEL, candidates, 'round-robin', before))
        .toEqual(expect.objectContaining({ providerId: 'steady' }));

      // Half-open: eligible again once the cooldown has passed.
      const after = before + CIRCUIT_COOLDOWN_MS + 1;
      const picked = Array.from({ length: 4 }, () =>
        service.selectRoute(MODEL, candidates, 'round-robin', after)?.providerId,
      );
      expect(picked).toContain('flaky');
    });

    it('does not count a success as a failure', () => {
      service.record(MODEL, 'provider-a', { ok: false });
      service.record(MODEL, 'provider-a', { ok: true });
      service.record(MODEL, 'provider-a', { ok: false });

      expect(service.isAvailable(MODEL, 'provider-a')).toBe(true);
    });
  });

  describe('per-provider reporting', () => {
    it('reports request counts, failures and average latency', () => {
      service.record(MODEL, 'provider-a', { ok: true, latencyMs: 100 });
      service.record(MODEL, 'provider-a', { ok: true, latencyMs: 300 });
      service.record(MODEL, 'provider-a', { ok: false, latencyMs: 50 });
      service.record(MODEL, 'provider-b', { ok: true, latencyMs: 20 });

      const rows = service.status(MODEL);
      const a = rows.find((r) => r.providerId === 'provider-a');
      const b = rows.find((r) => r.providerId === 'provider-b');

      expect(a).toEqual(expect.objectContaining({
        requests: 3, failures: 1, averageLatencyMs: 150, circuitOpen: false,
      }));
      expect(b).toEqual(expect.objectContaining({
        requests: 1, failures: 0, averageLatencyMs: 20,
      }));
    });

    it('reports no latency rather than zero when nothing was measured', () => {
      service.record(MODEL, 'provider-a', { ok: false });

      const row = service.status(MODEL)[0];
      expect(row?.averageLatencyMs).toBeNull();
    });

    it('reports the circuit as open while it is open', () => {
      for (let i = 0; i < FAILURES_BEFORE_OPEN; i += 1) {
        service.record(MODEL, 'provider-a', { ok: false });
      }

      const row = service.status(MODEL)[0];
      expect(row?.circuitOpen).toBe(true);
      expect(row?.circuitOpenedAt).not.toBeNull();
      expect(row?.consecutiveFailures).toBe(FAILURES_BEFORE_OPEN);
    });

    it('reports every provider when no model is named', () => {
      service.record(MODEL, 'provider-a', { ok: true, latencyMs: 10 });
      service.record('other-model', 'provider-b', { ok: true, latencyMs: 10 });

      expect(service.status().map((r) => r.providerId).sort())
        .toEqual(['provider-a', 'provider-b']);
    });

    it('forgets everything on reset', () => {
      service.record(MODEL, 'provider-a', { ok: false });
      service.reset();

      expect(service.status()).toEqual([]);
      expect(service.isAvailable(MODEL, 'provider-a')).toBe(true);
    });
  });
});


