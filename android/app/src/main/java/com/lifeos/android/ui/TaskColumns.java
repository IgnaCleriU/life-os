package com.lifeos.android.ui;

import com.lifeos.android.api.model.Priority;
import com.lifeos.android.api.model.Task;
import com.lifeos.android.api.model.TaskStatus;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/**
 * Splits the tasks of a project into the board columns. Pure Java, no Android types,
 * so it is covered by JVM tests.
 */
final class TaskColumns {

    /** The columns, left to right. */
    static final TaskStatus[] ORDER = {TaskStatus.TODO, TaskStatus.DOING, TaskStatus.DONE};

    /**
     * Inside a column: high priority first, then the earliest due date (tasks without one
     * last), then the oldest task, then id so the order is always the same.
     */
    static final Comparator<Task> SORT = Comparator
            .<Task>comparingInt(task -> priorityRank(task.getPriority()))
            .thenComparing(Task::getDueDate, Comparator.nullsLast(Comparator.<LocalDate>naturalOrder()))
            .thenComparing(Task::getCreatedAt, Comparator.nullsLast(Comparator.<Instant>naturalOrder()))
            .thenComparing(Task::getId, Comparator.nullsLast(Comparator.<String>naturalOrder()));

    private TaskColumns() {}

    /**
     * Every column present as a key, each sorted by {@link #SORT}. Tasks with an unknown
     * status (null) are left out: the board has no column for them.
     */
    static Map<TaskStatus, List<Task>> split(List<Task> tasks) {
        Map<TaskStatus, List<Task>> columns = new EnumMap<>(TaskStatus.class);
        for (TaskStatus status : TaskStatus.values()) {
            columns.put(status, new ArrayList<>());
        }
        if (tasks != null) {
            for (Task task : tasks) {
                if (task != null && task.getStatus() != null) {
                    columns.get(task.getStatus()).add(task);
                }
            }
        }
        for (List<Task> column : columns.values()) {
            column.sort(SORT);
        }
        return columns;
    }

    private static int priorityRank(Priority priority) {
        if (priority == null) {
            return 3;
        }
        switch (priority) {
            case HIGH:
                return 0;
            case MEDIUM:
                return 1;
            case LOW:
            default:
                return 2;
        }
    }
}
