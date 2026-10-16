package com.lifeos.android.api.model;

import java.time.Instant;

/**
 * A project as the REST API returns it. Immutable; fields are filled by Gson.
 * {@code status} is null if the server sends a value this app does not know.
 */
public final class Project {
    private final String id;
    private final String name;
    private final String description;
    private final ProjectStatus status;
    private final Instant createdAt;

    public Project(String id, String name, String description, ProjectStatus status, Instant createdAt) {
        this.id = id;
        this.name = name;
        this.description = description;
        this.status = status;
        this.createdAt = createdAt;
    }

    public String getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    /** May be null. */
    public String getDescription() {
        return description;
    }

    public ProjectStatus getStatus() {
        return status;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
