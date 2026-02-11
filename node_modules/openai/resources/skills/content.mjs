// File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.
import { APIResource } from "../../core/resource.mjs";
import { buildHeaders } from "../../internal/headers.mjs";
import { path } from "../../internal/utils/path.mjs";
export class Content extends APIResource {
    /**
     * Get Skill Content
     */
    retrieve(skillID, options) {
        return this._client.get(path `/skills/${skillID}/content`, {
            ...options,
            headers: buildHeaders([{ Accept: 'application/binary' }, options?.headers]),
            __binaryResponse: true,
        });
    }
}
//# sourceMappingURL=content.mjs.map