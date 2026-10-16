package com.lifeos.android.ui;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Menu;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.widget.PopupMenu;
import android.widget.ProgressBar;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;
import com.google.android.material.chip.ChipGroup;
import com.google.android.material.textfield.TextInputEditText;
import com.lifeos.android.R;
import com.lifeos.android.api.model.Project;
import com.lifeos.android.api.model.ProjectPatch;
import com.lifeos.android.api.model.ProjectStatus;
import com.lifeos.android.util.Async;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.Callable;

/**
 * Start destination: projects grouped by status, with an Active/All filter and a
 * search field. The list is reloaded on every resume, so changes made on the
 * board or in Settings show up when coming back.
 */
public class ProjectsFragment extends BaseFragment {

    static final String TAG = "projects";

    private static final String STATE_ACTIVE_ONLY = "activeOnly";
    private static final String STATE_QUERY = "query";
    /** Pause after the last keystroke before searching. */
    private static final long SEARCH_DELAY_MS = 300;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable searchRunnable = this::load;

    private boolean activeOnly = true;
    private String query = "";
    private Async.Call loadCall;

    private SwipeRefreshLayout swipeRefresh;
    private RecyclerView list;
    private TextView empty;
    private ProgressBar progress;
    private TextInputEditText searchInput;
    private ProjectsAdapter adapter;

    public ProjectsFragment() {
        super(R.layout.fragment_projects);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        ChipGroup filters = view.findViewById(R.id.filter_group);
        searchInput = view.findViewById(R.id.search_input);
        swipeRefresh = view.findViewById(R.id.swipe_refresh);
        list = view.findViewById(R.id.projects_list);
        empty = view.findViewById(R.id.projects_empty);
        progress = view.findViewById(R.id.projects_progress);

        if (savedInstanceState != null) {
            activeOnly = savedInstanceState.getBoolean(STATE_ACTIVE_ONLY, true);
            query = savedInstanceState.getString(STATE_QUERY, "");
        }
        filters.check(activeOnly ? R.id.chip_active : R.id.chip_all);
        searchInput.setText(query);

        filters.setOnCheckedStateChangeListener((group, checkedIds) -> {
            activeOnly = checkedIds.isEmpty() || checkedIds.get(0) == R.id.chip_active;
            load();
        });
        searchInput.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {}

            @Override
            public void afterTextChanged(Editable s) {
                query = String.valueOf(s).trim();
                handler.removeCallbacks(searchRunnable);
                handler.postDelayed(searchRunnable, SEARCH_DELAY_MS);
            }
        });
        searchInput.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                handler.removeCallbacks(searchRunnable);
                load();
                return true;
            }
            return false;
        });

        adapter = new ProjectsAdapter(new ProjectsAdapter.Listener() {
            @Override
            public void onOpen(Project project) {
                navigator().openProject(project.getId());
            }

            @Override
            public void onMore(View anchor, Project project) {
                showMenu(anchor, project);
            }
        });
        list.setLayoutManager(new LinearLayoutManager(requireContext()));
        list.setAdapter(adapter);
        swipeRefresh.setOnRefreshListener(this::load);

        view.findViewById(R.id.fab_new_project).setOnClickListener(v -> showCreateDialog());
    }

    @Override
    public void onResume() {
        super.onResume();
        setTitle(R.string.title_projects);
        load();
    }

    @Override
    public void onSaveInstanceState(@NonNull Bundle outState) {
        super.onSaveInstanceState(outState);
        outState.putBoolean(STATE_ACTIVE_ONLY, activeOnly);
        outState.putString(STATE_QUERY, query);
    }

    @Override
    public void onDestroyView() {
        handler.removeCallbacks(searchRunnable);
        super.onDestroyView();
    }

    /** Fetches the list for the current filter and search. A newer request cancels the one in flight. */
    private void load() {
        if (loadCall != null) {
            loadCall.cancel();
        }
        setLoading(true);
        List<ProjectStatus> statuses = activeOnly ? Collections.singletonList(ProjectStatus.ACTIVE) : null;
        String text = query.isEmpty() ? null : query;
        loadCall = async(() -> api().listProjects(statuses, text), new Async.Callback<List<Project>>() {
            @Override
            public void onSuccess(List<Project> projects) {
                setLoading(false);
                showProjects(projects);
            }

            @Override
            public void onError(Throwable error) {
                setLoading(false);
                showError(error);
            }
        });
    }

    private void setLoading(boolean loading) {
        if (loading) {
            empty.setVisibility(View.GONE);
        } else {
            swipeRefresh.setRefreshing(false);
        }
        // A pull-to-refresh already shows its own indicator.
        progress.setVisibility(loading && !swipeRefresh.isRefreshing() ? View.VISIBLE : View.GONE);
    }

    private void showProjects(List<Project> projects) {
        List<ProjectListItems.Item> items = ProjectListItems.build(projects);
        adapter.submit(items);
        if (items.isEmpty()) {
            empty.setText(emptyMessage());
            empty.setVisibility(View.VISIBLE);
        } else {
            empty.setVisibility(View.GONE);
        }
    }

    private String emptyMessage() {
        if (!query.isEmpty()) {
            return getString(R.string.projects_empty_search, query);
        }
        return getString(activeOnly ? R.string.projects_empty_active : R.string.projects_empty_none);
    }

    private void showCreateDialog() {
        ProjectFormDialog.show(requireContext(), R.string.dialog_project_new_title, "", "",
                (name, description) -> mutate(() -> api().createProject(name, description)));
    }

    private void showEditDialog(Project project) {
        String description = project.getDescription() == null ? "" : project.getDescription();
        ProjectFormDialog.show(requireContext(), R.string.dialog_project_edit_title,
                project.getName(), description, (name, newDescription) -> {
                    ProjectPatch patch = ProjectForm.changes(project, name, newDescription);
                    if (patch == null) {
                        return;
                    }
                    String id = project.getId();
                    mutate(() -> api().updateProject(id, patch));
                });
    }

    /** Row actions. Only Edit for now; the status actions and delete come next. */
    private void showMenu(View anchor, Project project) {
        PopupMenu popup = new PopupMenu(requireContext(), anchor);
        popup.getMenu().add(Menu.NONE, 0, 0, R.string.action_edit);
        popup.setOnMenuItemClickListener(item -> {
            showEditDialog(project);
            return true;
        });
        popup.show();
    }

    /** Runs a change, then reloads the list. Failures are shown; the list stays as it was. */
    private void mutate(Callable<Project> work) {
        async(work, new Async.Callback<Project>() {
            @Override
            public void onSuccess(Project result) {
                load();
            }

            @Override
            public void onError(Throwable error) {
                showError(error);
            }
        });
    }
}
