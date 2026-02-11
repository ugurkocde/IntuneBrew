"use strict";
// File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.
Object.defineProperty(exports, "__esModule", { value: true });
exports.Skills = void 0;
const tslib_1 = require("../../internal/tslib.js");
const resource_1 = require("../../core/resource.js");
const ContentAPI = tslib_1.__importStar(require("./content.js"));
const content_1 = require("./content.js");
const VersionsAPI = tslib_1.__importStar(require("./versions/versions.js"));
const versions_1 = require("./versions/versions.js");
const pagination_1 = require("../../core/pagination.js");
const uploads_1 = require("../../internal/uploads.js");
const path_1 = require("../../internal/utils/path.js");
class Skills extends resource_1.APIResource {
    constructor() {
        super(...arguments);
        this.content = new ContentAPI.Content(this._client);
        this.versions = new VersionsAPI.Versions(this._client);
    }
    /**
     * Create Skill
     */
    create(body = {}, options) {
        return this._client.post('/skills', (0, uploads_1.maybeMultipartFormRequestOptions)({ body, ...options }, this._client));
    }
    /**
     * Get Skill
     */
    retrieve(skillID, options) {
        return this._client.get((0, path_1.path) `/skills/${skillID}`, options);
    }
    /**
     * Update Skill Default Version
     */
    update(skillID, body, options) {
        return this._client.post((0, path_1.path) `/skills/${skillID}`, { body, ...options });
    }
    /**
     * List Skills
     */
    list(query = {}, options) {
        return this._client.getAPIList('/skills', (pagination_1.CursorPage), { query, ...options });
    }
    /**
     * Delete Skill
     */
    delete(skillID, options) {
        return this._client.delete((0, path_1.path) `/skills/${skillID}`, options);
    }
}
exports.Skills = Skills;
Skills.Content = content_1.Content;
Skills.Versions = versions_1.Versions;
//# sourceMappingURL=skills.js.map