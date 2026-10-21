package com.lifeos.android.ui;

import static org.junit.Assert.assertEquals;

import androidx.recyclerview.widget.RecyclerView;
import com.lifeos.android.api.model.Priority;
import com.lifeos.android.api.model.Task;
import com.lifeos.android.api.model.TaskStatus;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

/** A card must be rebound when midnight turns an unchanged task overdue. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = 35)
public class TaskCardAdapterTest {

    private static final LocalDate DUE = LocalDate.parse("2026-10-20");

    /** A clock the test can move forward. */
    private static final class MovableClock extends Clock {
        private Instant now;

        MovableClock(LocalDate day) {
            now = day.atStartOfDay(ZoneOffset.UTC).toInstant();
        }

        void setDay(LocalDate day) {
            now = day.atStartOfDay(ZoneOffset.UTC).toInstant();
        }

        @Override
        public ZoneId getZone() {
            return ZoneOffset.UTC;
        }

        @Override
        public Clock withZone(ZoneId zone) {
            return this;
        }

        @Override
        public Instant instant() {
            return now;
        }
    }

    private static final class CountingObserver extends RecyclerView.AdapterDataObserver {
        int changed;

        @Override
        public void onItemRangeChanged(int positionStart, int itemCount, Object payload) {
            changed += itemCount;
        }
    }

    private static List<Task> tasks() {
        return List.of(new Task("t1", "p1", "Pay rent", null, TaskStatus.TODO, Priority.MEDIUM, DUE,
                Instant.EPOCH));
    }

    @Test
    public void unchangedTaskIsReboundWhenItBecomesOverdue() {
        MovableClock clock = new MovableClock(DUE);
        TaskCardAdapter adapter = new TaskCardAdapter(task -> {}, clock);
        adapter.setItems(tasks());
        CountingObserver observer = new CountingObserver();
        adapter.registerAdapterDataObserver(observer);

        clock.setDay(DUE.plusDays(1));
        adapter.setItems(tasks());

        assertEquals(1, observer.changed);
    }

    @Test
    public void unchangedTaskOnTheSameDayIsLeftAlone() {
        MovableClock clock = new MovableClock(DUE);
        TaskCardAdapter adapter = new TaskCardAdapter(task -> {}, clock);
        adapter.setItems(tasks());
        CountingObserver observer = new CountingObserver();
        adapter.registerAdapterDataObserver(observer);

        adapter.setItems(tasks());

        assertEquals(0, observer.changed);
    }
}
