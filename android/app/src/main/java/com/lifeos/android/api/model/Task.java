package com.lifeos.android.api.model;

import java.time.Instant;
import java.time.LocalDate;

/**
 * A task as the REST API returns it. Immutable; fields are filled by Gson.
 * Enum fields are null if the server sends a value this app does not know.
 */
public final class Task {
    private final String id;
    private final String projectId;
    private final String title;
    private final String description;
    private final TaskStatus status;
    private final Priority priority;
    private final LocalDate dueDate;
    private final Instant createdAt;

    public Task(
            String id,
            String projectId,
            String title,
            String description,
            TaskStatus status,
            Priority priority,
            LocalDate dueDate,
            Instant createdAt) {
        this.id = id;
        this.projectId = projectId;
        this.title = title;
        this.description = description;
        this.status = status;
        this.priority = priority;
        this.dueDate = dueDate;
        this.createdAt = createdAt;
    }

    public String getId() {
        return id;
    }

    public String getProjectId() {
        return projectId;
    }

    public String getTitle() {
        return title;
    }

    /** May be null. */
    public String getDescription() {
        return description;
    }

    public TaskStatus getStatus() {
        return status;
    }

    public Priority getPriority() {
        return priority;
    }

    /** May be null. */
    public LocalDate getDueDate() {
        return dueDate;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
