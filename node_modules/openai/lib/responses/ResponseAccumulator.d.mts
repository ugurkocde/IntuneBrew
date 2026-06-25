import { type Response, type ResponseStreamEvent } from "../../resources/responses/responses.mjs";
/**
 * Applies a streaming event to a response snapshot.
 *
 * Always use the returned snapshot. Incremental events update the supplied snapshot
 * in place, while response lifecycle events return a detached replacement. Event
 * payloads are cloned, so retaining or replaying the raw events is safe.
 */
export declare function accumulateResponse(event: ResponseStreamEvent, snapshot?: Response): Response;
//# sourceMappingURL=ResponseAccumulator.d.mts.map