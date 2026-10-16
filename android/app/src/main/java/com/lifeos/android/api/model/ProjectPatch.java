package com.lifeos.android.api.model;

import com.google.gson.JsonNull;
import com.google.gson.JsonObject;

/**
 * Partial update of a project. Only the fields set on the builder are sent, so
 * an untouched field is left alone by the server. {@code description} can be
 * cleared explicitly (sent as JSON null). The name cannot be cleared: the
 * server ignores a null name.
 */
public final class ProjectPatch {
    private final JsonObject body = new JsonObject();

    public ProjectPatch name(String name) {
        body.addProperty("name", name);
        return this;
    }

    /** Sets the description; pass null to clear it. */
    public ProjectPatch description(String description) {
        if (description == null) {
            body.add("description", JsonNull.INSTANCE);
        } else {
            body.addProperty("description", description);
        }
        return this;
    }

    public ProjectPatch clearDescription() {
        return description(null);
    }

    public boolean isEmpty() {
        return body.size() == 0;
    }

    /** The JSON body to send. */
    public JsonObject toJson() {
        return body.deepCopy();
    }
}
