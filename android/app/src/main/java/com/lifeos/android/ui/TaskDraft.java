package com.lifeos.android.ui;

import com.lifeos.android.api.model.Priority;
import com.lifeos.android.api.model.Task;
import com.lifeos.android.api.model.TaskPatch;
import java.time.LocalDate;
import java.util.Objects;

/**
 * The values of the task form, as the user left them. Turns them into what the API needs:
 * a new task, or a patch that sends only the fields that changed. Pure Java.
 */
final class TaskDraft {

    private String title;
    private String description;
    private Priority priority;
    private LocalDate dueDate;

    private TaskDraft(String title, String description, Priority priority, LocalDate dueDate) {
        this.title = title;
        this.description = description;
        this.priority = priority;
        this.dueDate = dueDate;
    }

    /** Form for a new task: medium priority, no description, no due date. */
    static TaskDraft blank() {
        return new TaskDraft("", "", Priority.MEDIUM, null);
    }

    /** Form pre-filled from an existing task. */
    static TaskDraft of(Task task) {
        return new TaskDraft(
                nullToEmpty(task.getTitle()),
                nullToEmpty(task.getDescription()),
                task.getPriority(),
                task.getDueDate());
    }

    String getTitle() {
        return title;
    }

    void setTitle(String title) {
        this.title = nullToEmpty(title);
    }

    String getDescription() {
        return description;
    }

    void setDescription(String description) {
        this.description = nullToEmpty(description);
    }

    /** The priority, or medium when the task had none. */
    Priority priorityOrDefault() {
        return priority == null ? Priority.MEDIUM : priority;
    }

    void setPriority(Priority priority) {
        this.priority = priority;
    }

    /** Null means no due date. */
    LocalDate dueDate() {
        return dueDate;
    }

    void setDueDate(LocalDate dueDate) {
        this.dueDate = dueDate;
    }

    /** The title without surrounding spaces. */
    String trimmedTitle() {
        return title.trim();
    }

    /** A title is required: blank is rejected. */
    boolean hasTitle() {
        return !trimmedTitle().isEmpty();
    }

    /** The description trimmed, or null when it is blank. */
    String descriptionOrNull() {
        return normalizedDescription(description);
    }

    /**
     * The changes that turn {@code original} into this draft. Empty when nothing changed, so
     * an unchanged form does not call the server. Priority is only sent when it was set.
     */
    TaskPatch changesFrom(Task original) {
        TaskPatch patch = new TaskPatch();

        String originalTitle = nullToEmpty(original.getTitle()).trim();
        if (!trimmedTitle().equals(originalTitle)) {
            patch.title(trimmedTitle());
        }
        if (priority != null && priority != original.getPriority()) {
            patch.priority(priority);
        }
        String newDescription = normalizedDescription(description);
        String oldDescription = normalizedDescription(original.getDescription());
        if (!Objects.equals(newDescription, oldDescription)) {
            patch.description(newDescription);
        }
        if (!Objects.equals(dueDate, original.getDueDate())) {
            patch.dueDate(dueDate);
        }
        return patch;
    }

    private static String normalizedDescription(String value) {
        String trimmed = nullToEmpty(value).trim();
        return trimmed.isEmpty() ? null : trimmed;
    }

    private static String nullToEmpty(String value) {
        return value == null ? "" : value;
    }
}
