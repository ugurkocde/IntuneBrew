// File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.
import { APIResource } from "../../../core/resource.mjs";
import * as ContentAPI from "./content.mjs";
import { Content } from "./content.mjs";
import { CursorPage } from "../../../core/pagination.mjs";
import { maybeMultipartFormRequestOptions } from "../../../internal/uploads.mjs";
import { path } from "../../../internal/utils/path.mjs";
export class Versions extends APIResource {
    constructor() {
        super(...arguments);
        this.content = new ContentAPI.Content(this._client);
    }
    /**
     * Create Skill Version
     */
    create(skillID, body = {}, options) {
        return this._client.post(path `/skills/${skillID}/versions`, maybeMultipartFormRequestOptions({ body, ...options }, this._client));
    }
    /**
     * Get Skill Version
     */
    retrieve(version, params, options) {
        const { skill_id } = params;
        return this._client.get(path `/skills/${skill_id}/versions/${version}`, options);
    }
    /**
     * List Skill Versions
     */
    list(skillID, query = {}, options) {
        return this._client.getAPIList(path `/skills/${skillID}/versions`, (CursorPage), {
            query,
            ...options,
        });
    }
    /**
     * Delete Skill Version
     */
    delete(version, params, options) {
        const { skill_id } = params;
        return this._client.delete(path `/skills/${skill_id}/versions/${version}`, options);
    }
}
Versions.Content = Content;
//# sourceMappingURL=versions.mjs.map