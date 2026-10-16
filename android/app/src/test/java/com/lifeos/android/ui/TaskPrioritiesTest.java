package com.lifeos.android.ui;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotEquals;

import com.lifeos.android.R;
import com.lifeos.android.api.model.Priority;
import java.util.HashSet;
import java.util.Set;
import org.junit.Test;

public class TaskPrioritiesTest {

    @Test
    public void eachPriorityHasItsOwnLabel() {
        assertEquals(R.string.task_priority_low, TaskPriorities.labelRes(Priority.LOW));
        assertEquals(R.string.task_priority_medium, TaskPriorities.labelRes(Priority.MEDIUM));
        assertEquals(R.string.task_priority_high, TaskPriorities.labelRes(Priority.HIGH));
        assertNotEquals(TaskPriorities.labelRes(Priority.LOW), TaskPriorities.labelRes(Priority.HIGH));
    }

    @Test
    public void dropdownOrderCoversEveryPriorityOnce() {
        Set<Priority> seen = new HashSet<>();
        for (Priority priority : TaskPriorities.ORDER) {
            seen.add(priority);
        }
        assertEquals(Priority.values().length, TaskPriorities.ORDER.length);
        assertEquals(Priority.values().length, seen.size());
        assertEquals(Priority.LOW, TaskPriorities.ORDER[0]);
        assertEquals(Priority.HIGH, TaskPriorities.ORDER[2]);
    }
}
