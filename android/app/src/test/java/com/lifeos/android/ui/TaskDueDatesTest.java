package com.lifeos.android.ui;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import com.lifeos.android.api.model.Priority;
import com.lifeos.android.api.model.Task;
import com.lifeos.android.api.model.TaskStatus;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import org.junit.Test;

public class TaskDueDatesTest {

    private static final LocalDate TODAY = LocalDate.parse("2026-10-16");

    private static Clock clockAt(String day) {
        return Clock.fixed(LocalDate.parse(day).atTime(9, 30).toInstant(ZoneOffset.UTC), ZoneOffset.UTC);
    }

    private static Task task(TaskStatus status, LocalDate due) {
        return new Task("id", "p1", "t", null, status, Priority.MEDIUM, due, Instant.EPOCH);
    }

    @Test
    public void pastDueOpenTaskIsOverdue() {
        assertTrue(TaskDueDates.isOverdue(TaskStatus.TODO, LocalDate.parse("2026-10-15"), TODAY));
        assertTrue(TaskDueDates.isOverdue(TaskStatus.DOING, LocalDate.parse("2026-01-01"), TODAY));
    }

    @Test
    public void dueTodayIsNotOverdue() {
        assertFalse(TaskDueDates.isOverdue(TaskStatus.TODO, TODAY, TODAY));
    }

    @Test
    public void futureOrMissingDueDateIsNotOverdue() {
        assertFalse(TaskDueDates.isOverdue(TaskStatus.TODO, LocalDate.parse("2026-10-17"), TODAY));
        assertFalse(TaskDueDates.isOverdue(TaskStatus.TODO, null, TODAY));
    }

    @Test
    public void doneTaskIsNeverOverdue() {
        assertFalse(TaskDueDates.isOverdue(TaskStatus.DONE, LocalDate.parse("2026-01-01"), TODAY));
    }

    @Test
    public void overdueUsesTheInjectedClock() {
        Task due = task(TaskStatus.TODO, LocalDate.parse("2026-10-16"));

        assertFalse(TaskDueDates.isOverdue(due, clockAt("2026-10-16")));
        assertTrue(TaskDueDates.isOverdue(due, clockAt("2026-10-17")));
        assertFalse(TaskDueDates.isOverdue(due, clockAt("2026-10-15")));
    }

    @Test
    public void utcMillisRoundTripToTheSameDay() {
        LocalDate day = LocalDate.parse("2026-02-28");

        long millis = TaskDueDates.toUtcMillis(day);

        assertEquals(day, TaskDueDates.fromUtcMillis(millis));
        assertEquals(Instant.parse("2026-02-28T00:00:00Z").toEpochMilli(), millis);
    }
}
