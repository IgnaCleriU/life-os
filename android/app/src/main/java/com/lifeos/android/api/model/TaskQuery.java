package com.lifeos.android.api.model;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Filters for listing tasks; every field is optional. Immutable once built. */
public final class TaskQuery {
    private final List<TaskStatus> statuses;
    private final String text;
    private final LocalDate dueBefore;
    private final String projectId;

    private TaskQuery(Builder b) {
        this.statuses = Collections.unmodifiableList(new ArrayList<>(b.statuses));
        this.text = b.text;
        this.dueBefore = b.dueBefore;
        this.projectId = b.projectId;
    }

    /** No filters. */
    public static TaskQuery all() {
        return new Builder().build();
    }

    public static Builder builder() {
        return new Builder();
    }

    /** Empty means "any status". */
    public List<TaskStatus> getStatuses() {
        return statuses;
    }

    /** Free-text search ({@code q}), or null. */
    public String getText() {
        return text;
    }

    /** Only tasks due strictly before this date ({@code due_before}), or null. */
    public LocalDate getDueBefore() {
        return dueBefore;
    }

    /** Only used by {@code GET /tasks}; the per-project listing takes the id from its path. */
    public String getProjectId() {
        return projectId;
    }

    public static final class Builder {
        private final List<TaskStatus> statuses = new ArrayList<>();
        private String text;
        private LocalDate dueBefore;
        private String projectId;

        public Builder status(TaskStatus status) {
            statuses.add(status);
            return this;
        }

        public Builder statuses(List<TaskStatus> values) {
            statuses.addAll(values);
            return this;
        }

        public Builder text(String text) {
            this.text = text;
            return this;
        }

        public Builder dueBefore(LocalDate dueBefore) {
            this.dueBefore = dueBefore;
            return this;
        }

        public Builder projectId(String projectId) {
            this.projectId = projectId;
            return this;
        }

        public TaskQuery build() {
            return new TaskQuery(this);
        }
    }
}
