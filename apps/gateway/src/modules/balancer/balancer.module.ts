import { Module } from '@nestjs/common';
import { RoutesModule } from '../routes/routes.module';
import { LoadBalancerService } from './load-balancer.service';

/**
 * Choosing between the providers that can serve a model.
 *
 * Imports `RoutesModule` so the balancer can ask for every candidate rather than
 * the single one the proxy used to take, and exports the service so the proxy
 * controller can ask it for a route.
 */
@Module({
  imports: [RoutesModule],
  providers: [LoadBalancerService],
  exports: [LoadBalancerService],
})
export class BalancerModule {}
