package com.lifeos.android.ui;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.annotation.StringRes;
import androidx.recyclerview.widget.RecyclerView;
import com.google.android.material.chip.Chip;
import com.lifeos.android.R;
import com.lifeos.android.api.model.Project;
import com.lifeos.android.api.model.ProjectStatus;
import java.util.ArrayList;
import java.util.List;

/** Rows of the Projects list: section headers and project rows. */
final class ProjectsAdapter extends RecyclerView.Adapter<RecyclerView.ViewHolder> {

    interface Listener {
        void onOpen(Project project);

        /** The overflow button or a long press on the row; {@code anchor} is where the menu hangs. */
        void onMore(View anchor, Project project);
    }

    private static final int TYPE_HEADER = 0;
    private static final int TYPE_PROJECT = 1;

    private final List<ProjectListItems.Item> items = new ArrayList<>();
    private final Listener listener;

    ProjectsAdapter(Listener listener) {
        this.listener = listener;
    }

    void submit(List<ProjectListItems.Item> newItems) {
        items.clear();
        items.addAll(newItems);
        notifyDataSetChanged();
    }

    /** The label of a status, shared by section headers and status chips. */
    @StringRes
    static int statusLabel(ProjectStatus status) {
        // Callers pass only known statuses: ProjectListItems leaves the unknown ones out.
        switch (status) {
            case COMPLETED:
                return R.string.status_completed;
            case ARCHIVED:
                return R.string.status_archived;
            case ACTIVE:
            default:
                return R.string.status_active;
        }
    }

    @Override
    public int getItemCount() {
        return items.size();
    }

    @Override
    public int getItemViewType(int position) {
        return items.get(position).isHeader() ? TYPE_HEADER : TYPE_PROJECT;
    }

    @NonNull
    @Override
    public RecyclerView.ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        LayoutInflater inflater = LayoutInflater.from(parent.getContext());
        if (viewType == TYPE_HEADER) {
            return new HeaderHolder(inflater.inflate(R.layout.item_project_header, parent, false));
        }
        return new ProjectHolder(inflater.inflate(R.layout.item_project, parent, false));
    }

    @Override
    public void onBindViewHolder(@NonNull RecyclerView.ViewHolder holder, int position) {
        ProjectListItems.Item item = items.get(position);
        if (holder instanceof HeaderHolder) {
            ((HeaderHolder) holder).bind(item.getStatus());
        } else {
            ((ProjectHolder) holder).bind(item.getProject());
        }
    }

    private static final class HeaderHolder extends RecyclerView.ViewHolder {
        private final TextView title;

        HeaderHolder(View itemView) {
            super(itemView);
            title = itemView.findViewById(R.id.item_project_header_title);
        }

        void bind(ProjectStatus section) {
            title.setText(statusLabel(section));
        }
    }

    private final class ProjectHolder extends RecyclerView.ViewHolder {
        private final TextView name;
        private final TextView description;
        private final Chip status;
        private final View more;

        ProjectHolder(View itemView) {
            super(itemView);
            name = itemView.findViewById(R.id.item_project_name);
            description = itemView.findViewById(R.id.item_project_description);
            status = itemView.findViewById(R.id.item_project_status);
            more = itemView.findViewById(R.id.item_project_more);
        }

        void bind(Project project) {
            name.setText(project.getName());
            String text = project.getDescription() == null ? "" : project.getDescription().trim();
            description.setText(text);
            description.setVisibility(text.isEmpty() ? View.GONE : View.VISIBLE);
            status.setText(statusLabel(project.getStatus()));
            itemView.setOnClickListener(v -> listener.onOpen(project));
            itemView.setOnLongClickListener(v -> {
                listener.onMore(itemView, project);
                return true;
            });
            more.setOnClickListener(v -> listener.onMore(more, project));
        }
    }
}
