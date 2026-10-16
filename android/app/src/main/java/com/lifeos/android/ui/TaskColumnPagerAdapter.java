package com.lifeos.android.ui;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.annotation.StringRes;
import androidx.recyclerview.widget.RecyclerView;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;
import com.lifeos.android.R;
import com.lifeos.android.api.model.Task;
import com.lifeos.android.api.model.TaskStatus;
import java.time.Clock;
import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * Pages of the board: one page per column in {@link TaskColumns#ORDER}. Each page has its own
 * pull-to-refresh and card list; the board hands it the already-split tasks.
 */
final class TaskColumnPagerAdapter extends RecyclerView.Adapter<TaskColumnPagerAdapter.Holder> {

    interface Listener {
        void onTaskClicked(Task task);

        void onRefresh();
    }

    /** Payload of an in-place refresh: lets RecyclerView reuse the page instead of recreating it. */
    private static final Object REFRESH = new Object();

    private final Listener listener;
    private final Clock clock;
    private Map<TaskStatus, List<Task>> columns = Collections.emptyMap();
    private boolean loading;

    TaskColumnPagerAdapter(Listener listener, Clock clock) {
        this.listener = listener;
        this.clock = clock;
    }

    /** Title of a column, shown on its tab. */
    static @StringRes int titleRes(TaskStatus status) {
        switch (status) {
            case DOING:
                return R.string.task_column_doing;
            case DONE:
                return R.string.task_column_done;
            case TODO:
            default:
                return R.string.task_column_todo;
        }
    }

    /**
     * Replaces the tasks shown on every page and whether a reload is running. The pages are
     * updated in place (a payload change keeps their views), so their lists keep scrolling.
     */
    void setState(Map<TaskStatus, List<Task>> columns, boolean loading) {
        this.columns = columns;
        this.loading = loading;
        notifyItemRangeChanged(0, getItemCount(), REFRESH);
    }

    @NonNull
    @Override
    public Holder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.fragment_task_column, parent, false);
        return new Holder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull Holder holder, int position) {
        TaskStatus status = TaskColumns.ORDER[position];
        List<Task> tasks = columns.getOrDefault(status, Collections.emptyList());
        holder.bind(tasks, loading);
    }

    @Override
    public int getItemCount() {
        return TaskColumns.ORDER.length;
    }

    final class Holder extends RecyclerView.ViewHolder {

        private final SwipeRefreshLayout refresh;
        private final RecyclerView list;
        private final TextView empty;
        private final TaskCardAdapter cards;

        Holder(View view) {
            super(view);
            refresh = view.findViewById(R.id.task_column_refresh);
            list = view.findViewById(R.id.task_column_list);
            empty = view.findViewById(R.id.task_column_empty);
            cards = new TaskCardAdapter(listener::onTaskClicked, clock);
            list.setAdapter(cards);
            // The wrapper around the list is not scrollable, so tell pull-to-refresh whether the
            // list is at its top; otherwise a swipe from deep in the list would refresh.
            refresh.setOnChildScrollUpCallback((parent, child) -> list.canScrollVertically(-1));
            refresh.setOnRefreshListener(listener::onRefresh);
        }

        void bind(List<Task> tasks, boolean loading) {
            cards.setItems(tasks);
            boolean isEmpty = tasks.isEmpty();
            list.setVisibility(isEmpty ? View.GONE : View.VISIBLE);
            // Not while loading: the first load would flash "No tasks" before any task arrives.
            empty.setVisibility(isEmpty && !loading ? View.VISIBLE : View.GONE);
            refresh.setRefreshing(loading);
        }
    }
}
