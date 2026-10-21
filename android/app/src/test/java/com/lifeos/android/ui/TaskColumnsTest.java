package com.lifeos.android.ui;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import com.lifeos.android.api.model.Priority;
import com.lifeos.android.api.model.Task;
import com.lifeos.android.api.model.TaskStatus;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import org.junit.Test;

public class TaskColumnsTest {

    private static final Instant T0 = Instant.parse("2026-10-01T10:00:00Z");

    private static Task task(String id, TaskStatus status, Priority priority, LocalDate due, Instant created) {
        return new Task(id, "p1", "title " + id, null, status, priority, due, created);
    }

    @Test
    public void everyColumnIsPresentEvenWhenEmpty() {
        Map<TaskStatus, List<Task>> columns = TaskColumns.split(List.of());

        for (TaskStatus status : TaskColumns.ORDER) {
            assertTrue(columns.get(status).isEmpty());
        }
        assertEquals(3, columns.size());
    }

    @Test
    public void nullListIsTreatedAsEmpty() {
        assertTrue(TaskColumns.split(null).get(TaskStatus.TODO).isEmpty());
    }

    @Test
    public void tasksGoToTheColumnOfTheirStatus() {
        Task todo = task("a", TaskStatus.TODO, Priority.LOW, null, T0);
        Task doing = task("b", TaskStatus.DOING, Priority.LOW, null, T0);
        Task done = task("c", TaskStatus.DONE, Priority.LOW, null, T0);

        Map<TaskStatus, List<Task>> columns = TaskColumns.split(Arrays.asList(done, todo, doing));

        assertEquals(List.of(todo), columns.get(TaskStatus.TODO));
        assertEquals(List.of(doing), columns.get(TaskStatus.DOING));
        assertEquals(List.of(done), columns.get(TaskStatus.DONE));
    }

    @Test
    public void tasksWithUnknownStatusAreLeftOut() {
        Task unknown = task("x", null, Priority.HIGH, null, T0);
        Task todo = task("a", TaskStatus.TODO, Priority.LOW, null, T0);

        Map<TaskStatus, List<Task>> columns = TaskColumns.split(Arrays.asList(unknown, null, todo));

        assertEquals(List.of(todo), columns.get(TaskStatus.TODO));
        int placed = 0;
        for (TaskStatus status : TaskColumns.ORDER) {
            placed += columns.get(status).size();
        }
        assertEquals(1, placed);
    }

    @Test
    public void sortsByPriorityHighestFirst() {
        Task low = task("low", TaskStatus.TODO, Priority.LOW, null, T0);
        Task high = task("high", TaskStatus.TODO, Priority.HIGH, null, T0);
        Task medium = task("medium", TaskStatus.TODO, Priority.MEDIUM, null, T0);

        List<Task> todo = TaskColumns.split(Arrays.asList(low, medium, high)).get(TaskStatus.TODO);

        assertEquals(Arrays.asList(high, medium, low), todo);
    }

    @Test
    public void withinAPriorityEarliestDueDateFirstAndNoDueDateLast() {
        LocalDate day1 = LocalDate.parse("2026-10-05");
        LocalDate day2 = LocalDate.parse("2026-10-20");
        Task late = task("late", TaskStatus.TODO, Priority.MEDIUM, day2, T0);
        Task none = task("none", TaskStatus.TODO, Priority.MEDIUM, null, T0);
        Task early = task("early", TaskStatus.TODO, Priority.MEDIUM, day1, T0);

        List<Task> todo = TaskColumns.split(Arrays.asList(none, late, early)).get(TaskStatus.TODO);

        assertEquals(Arrays.asList(early, late, none), todo);
    }

    @Test
    public void tiesAreBrokenByCreationTimeThenId() {
        Task newer = task("a", TaskStatus.DOING, Priority.HIGH, null, T0.plusSeconds(60));
        Task olderB = task("b", TaskStatus.DOING, Priority.HIGH, null, T0);
        Task olderA = task("a2", TaskStatus.DOING, Priority.HIGH, null, T0);

        List<Task> doing = new ArrayList<>(TaskColumns.split(Arrays.asList(newer, olderB, olderA)).get(TaskStatus.DOING));

        assertEquals(Arrays.asList(olderA, olderB, newer), doing);
    }

    @Test
    public void unknownPriorityGoesAfterLow() {
        Task unknown = task("u", TaskStatus.TODO, null, null, T0);
        Task low = task("l", TaskStatus.TODO, Priority.LOW, null, T0);

        List<Task> todo = TaskColumns.split(Arrays.asList(unknown, low)).get(TaskStatus.TODO);

        assertEquals(Arrays.asList(low, unknown), todo);
    }
}
