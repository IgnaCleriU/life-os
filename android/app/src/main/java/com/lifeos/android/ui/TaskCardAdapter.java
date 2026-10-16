package com.lifeos.android.ui;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import com.google.android.material.color.MaterialColors;
import com.lifeos.android.R;
import com.lifeos.android.api.model.Priority;
import com.lifeos.android.api.model.Task;
import java.time.Clock;
import java.time.format.DateTimeFormatter;
import java.time.format.FormatStyle;
import java.util.Collections;
import java.util.List;

/** Task cards of one board column. */
final class TaskCardAdapter extends RecyclerView.Adapter<TaskCardAdapter.Holder> {

    interface Listener {
        void onTaskClicked(Task task);
    }

    private final Listener listener;
    private final Clock clock;
    private List<Task> items = Collections.emptyList();

    TaskCardAdapter(Listener listener, Clock clock) {
        this.listener = listener;
        this.clock = clock;
    }

    void setItems(List<Task> tasks) {
        items = tasks;
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public Holder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_task, parent, false);
        return new Holder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull Holder holder, int position) {
        holder.bind(items.get(position));
    }

    @Override
    public int getItemCount() {
        return items.size();
    }

    final class Holder extends RecyclerView.ViewHolder {

        private final TextView title;
        private final TextView description;
        private final TextView priority;
        private final TextView due;

        Holder(View view) {
            super(view);
            title = view.findViewById(R.id.item_task_title);
            description = view.findViewById(R.id.item_task_description);
            priority = view.findViewById(R.id.item_task_priority);
            due = view.findViewById(R.id.item_task_due);
        }

        void bind(Task task) {
            Context context = itemView.getContext();
            title.setText(task.getTitle());

            String text = task.getDescription();
            boolean hasDescription = text != null && !text.trim().isEmpty();
            description.setVisibility(hasDescription ? View.VISIBLE : View.GONE);
            description.setText(hasDescription ? text.trim() : null);

            bindPriority(context, task.getPriority());
            bindDue(context, task);

            itemView.setOnClickListener(v -> listener.onTaskClicked(task));
        }

        private void bindPriority(Context context, Priority value) {
            if (value == null) {
                priority.setVisibility(View.GONE);
                return;
            }
            priority.setVisibility(View.VISIBLE);
            String[] labels = context.getResources().getStringArray(R.array.task_priority_labels);
            priority.setText(labels[value.ordinal()]);
            int attr;
            switch (value) {
                case HIGH:
                    attr = androidx.appcompat.R.attr.colorError;
                    break;
                case MEDIUM:
                    attr = androidx.appcompat.R.attr.colorPrimary;
                    break;
                case LOW:
                default:
                    attr = com.google.android.material.R.attr.colorOnSurfaceVariant;
                    break;
            }
            priority.setTextColor(MaterialColors.getColor(priority, attr));
        }

        private void bindDue(Context context, Task task) {
            if (task.getDueDate() == null) {
                due.setVisibility(View.GONE);
                return;
            }
            due.setVisibility(View.VISIBLE);
            String date = DateTimeFormatter.ofLocalizedDate(FormatStyle.MEDIUM).format(task.getDueDate());
            boolean overdue = TaskDueDates.isOverdue(task, clock);
            due.setText(context.getString(
                    overdue ? R.string.task_overdue : R.string.task_due, date));
            int attr = overdue
                    ? androidx.appcompat.R.attr.colorError
                    : com.google.android.material.R.attr.colorOnSurfaceVariant;
            due.setTextColor(MaterialColors.getColor(due, attr));
        }
    }
}
