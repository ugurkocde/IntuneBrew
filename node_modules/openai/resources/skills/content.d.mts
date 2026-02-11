import { APIResource } from "../../core/resource.mjs";
import { APIPromise } from "../../core/api-promise.mjs";
import { RequestOptions } from "../../internal/request-options.mjs";
export declare class Content extends APIResource {
    /**
     * Get Skill Content
     */
    retrieve(skillID: string, options?: RequestOptions): APIPromise<Response>;
}
//# sourceMappingURL=content.d.mts.map