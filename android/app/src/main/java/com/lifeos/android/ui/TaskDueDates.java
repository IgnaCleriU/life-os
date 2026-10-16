package com.lifeos.android.ui;

import com.lifeos.android.api.model.Task;
import com.lifeos.android.api.model.TaskStatus;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.time.format.FormatStyle;

/**
 * Due-date rules. The clock is a parameter so "today" can be fixed in tests. Pure Java.
 */
final class TaskDueDates {

    /** Shared by the cards and the form: built once, not on every bind. */
    private static final DateTimeFormatter DISPLAY = DateTimeFormatter.ofLocalizedDate(FormatStyle.MEDIUM);

    private TaskDueDates() {}

    /** The date as shown to the user (medium localized style). */
    static String format(LocalDate date) {
        return DISPLAY.format(date);
    }

    /** A task is overdue when it has a due date before today and is not done. */
    static boolean isOverdue(Task task, Clock clock) {
        return isOverdue(task.getStatus(), task.getDueDate(), LocalDate.now(clock));
    }

    static boolean isOverdue(TaskStatus status, LocalDate dueDate, LocalDate today) {
        return dueDate != null && status != TaskStatus.DONE && dueDate.isBefore(today);
    }

    /**
     * The date picker works in UTC midnight millis, so a date is stored as its UTC day
     * and read back the same way, whatever the device time zone.
     */
    static long toUtcMillis(LocalDate date) {
        return date.atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli();
    }

    static LocalDate fromUtcMillis(long millis) {
        return Instant.ofEpochMilli(millis).atZone(ZoneOffset.UTC).toLocalDate();
    }
}
