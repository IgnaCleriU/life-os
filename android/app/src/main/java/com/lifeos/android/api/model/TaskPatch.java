package com.lifeos.android.api.model;

import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.time.LocalDate;

/**
 * Partial update of a task. Only the fields set on the builder are sent, so
 * an untouched field is left alone by the server. {@code description} and
 * {@code dueDate} can be cleared explicitly (sent as JSON null). Title and
 * priority cannot be cleared. Status changes go through the start / complete /
 * reopen endpoints, not through a patch.
 */
public final class TaskPatch {
    private final JsonObject body = new JsonObject();

    public TaskPatch title(String title) {
        body.addProperty("title", title);
        return this;
    }

    public TaskPatch priority(Priority priority) {
        body.addProperty("priority", priority.value());
        return this;
    }

    /** Sets the description; pass null to clear it. */
    public TaskPatch description(String description) {
        if (description == null) {
            body.add("description", JsonNull.INSTANCE);
        } else {
            body.addProperty("description", description);
        }
        return this;
    }

    public TaskPatch clearDescription() {
        return description(null);
    }

    /** Sets the due date; pass null to clear it. */
    public TaskPatch dueDate(LocalDate dueDate) {
        if (dueDate == null) {
            body.add("due_date", JsonNull.INSTANCE);
        } else {
            body.addProperty("due_date", dueDate.toString());
        }
        return this;
    }

    public TaskPatch clearDueDate() {
        return dueDate(null);
    }

    public boolean isEmpty() {
        return body.size() == 0;
    }

    /** The JSON body to send. */
    public JsonObject toJson() {
        return body.deepCopy();
    }
}
