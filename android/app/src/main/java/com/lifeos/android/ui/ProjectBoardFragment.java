package com.lifeos.android.ui;

import android.os.Bundle;
import android.view.View;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.annotation.StringRes;
import androidx.viewpager2.widget.ViewPager2;
import com.google.android.material.dialog.MaterialAlertDialogBuilder;
import com.google.android.material.floatingactionbutton.ExtendedFloatingActionButton;
import com.google.android.material.tabs.TabLayout;
import com.google.android.material.tabs.TabLayoutMediator;
import com.lifeos.android.R;
import com.lifeos.android.api.model.Priority;
import com.lifeos.android.api.model.Project;
import com.lifeos.android.api.model.ProjectStatus;
import com.lifeos.android.api.model.Task;
import com.lifeos.android.api.model.TaskPatch;
import com.lifeos.android.api.model.TaskQuery;
import com.lifeos.android.api.model.TaskStatus;
import com.lifeos.android.util.Async;
import com.lifeos.android.util.Snackbars;
import java.time.Clock;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Callable;

/**
 * Task board of one project: three swipeable columns (To do / Doing / Done). All tasks are
 * loaded once and split by status here. Open it with {@code Navigator.openProject(id)}.
 */
public class ProjectBoardFragment extends BaseFragment {

    static final String TAG = "project_board";
    private static final String ARG_PROJECT_ID = "project_id";

    private final Clock clock = Clock.systemDefaultZone();

    /** Page index of the To do column: new tasks are created there. */
    private static final int TODO_PAGE = 0;

    private TabLayout tabs;
    private ViewPager2 pager;
    private TaskColumnPagerAdapter columnAdapter;
    private TabLayoutMediator tabMediator;

    /** Last loaded state, kept across view re-creation (rotation). */
    private List<Task> tasks = List.of();
    private String projectName;
    private boolean loading;
    private int loadSeq;
    private int appliedSeq;

    public static ProjectBoardFragment newInstance(String projectId) {
        ProjectBoardFragment fragment = new ProjectBoardFragment();
        Bundle args = new Bundle();
        args.putString(ARG_PROJECT_ID, projectId);
        fragment.setArguments(args);
        return fragment;
    }

    public ProjectBoardFragment() {
        super(R.layout.fragment_project_board);
    }

    /** The project this board shows. */
    public String getProjectId() {
        return requireArguments().getString(ARG_PROJECT_ID);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        tabs = view.findViewById(R.id.task_board_tabs);
        pager = view.findViewById(R.id.task_board_pager);
        columnAdapter = new TaskColumnPagerAdapter(new TaskColumnPagerAdapter.Listener() {
            @Override
            public void onTaskClicked(Task task) {
                showActions(task);
            }

            @Override
            public void onRefresh() {
                loadBoard();
            }
        }, clock);
        pager.setAdapter(columnAdapter);
        tabMediator = new TabLayoutMediator(tabs, pager, (tab, position) ->
                tab.setText(tabTitle(position, TaskColumns.split(tasks))));
        tabMediator.attach();

        ExtendedFloatingActionButton newTask = view.findViewById(R.id.task_board_new);
        newTask.setOnClickListener(v -> showEditor(null));

        render();
        loadBoard();
    }

    @Override
    public void onResume() {
        super.onResume();
        if (projectName != null) {
            setTitle(projectName);
        } else {
            setTitle(R.string.title_board);
        }
    }

    @Override
    public void onDestroyView() {
        if (tabMediator != null) {
            tabMediator.detach();
            tabMediator = null;
        }
        super.onDestroyView();
    }

    /** Loads the project name and all of its tasks; the newest response wins. */
    void loadBoard() {
        int seq = ++loadSeq;
        String projectId = getProjectId();
        setLoading(true);
        async(() -> {
            Project project = api().getProject(projectId);
            List<Task> all = api().listProjectTasks(projectId, TaskQuery.all());
            return new Board(project, all);
        }, new Async.Callback<Board>() {
            @Override
            public void onSuccess(Board board) {
                if (seq < appliedSeq) {
                    return;
                }
                appliedSeq = seq;
                projectName = board.project.getName();
                tasks = board.tasks;
                setTitle(projectName);
                setLoading(false);
            }

            @Override
            public void onError(Throwable error) {
                if (seq == loadSeq) {
                    setLoading(false);
                }
                showError(error);
            }
        });
    }

    /** The action menu of a task: only the actions that make sense for its column. */
    private void showActions(Task task) {
        List<TaskMenu.Action> actions = TaskMenu.actionsFor(task.getStatus());
        String[] labels = new String[actions.size()];
        for (int i = 0; i < labels.length; i++) {
            labels[i] = getString(labelRes(actions.get(i)));
        }
        new MaterialAlertDialogBuilder(requireContext())
                .setTitle(task.getTitle())
                .setItems(labels, (dialog, which) -> perform(task, actions.get(which)))
                .show();
    }

    private static @StringRes int labelRes(TaskMenu.Action action) {
        switch (action) {
            case START:
                return R.string.task_action_start;
            case COMPLETE:
                return R.string.task_action_complete;
            case REOPEN:
                return R.string.task_action_reopen;
            case EDIT:
                return R.string.task_action_edit;
            case MOVE:
                return R.string.task_action_move;
            case DELETE:
            default:
                return R.string.task_action_delete;
        }
    }

    private void perform(Task task, TaskMenu.Action action) {
        String taskId = task.getId();
        switch (action) {
            case START:
                runThenReload(() -> api().startTask(taskId));
                break;
            case COMPLETE:
                runThenReload(() -> api().completeTask(taskId));
                break;
            case REOPEN:
                runThenReload(() -> api().reopenTask(taskId));
                break;
            case EDIT:
                showEditor(task);
                break;
            case MOVE:
                chooseMoveTarget(task);
                break;
            case DELETE:
            default:
                confirmDelete(task);
                break;
        }
    }

    private void chooseMoveTarget(Task task) {
        String currentProjectId = getProjectId();
        String taskId = task.getId();
        async(() -> api().listProjects(List.of(ProjectStatus.ACTIVE), null), new Async.Callback<List<Project>>() {
            @Override
            public void onSuccess(List<Project> projects) {
                List<Project> targets = TaskMenu.moveTargets(projects, currentProjectId);
                if (targets.isEmpty()) {
                    Snackbars.info(requireView(), getString(R.string.task_move_none));
                    return;
                }
                String[] names = new String[targets.size()];
                for (int i = 0; i < names.length; i++) {
                    names[i] = targets.get(i).getName();
                }
                new MaterialAlertDialogBuilder(requireContext())
                        .setTitle(R.string.task_move_title)
                        .setItems(names, (dialog, which) -> moveTask(taskId, targets.get(which)))
                        .setNegativeButton(android.R.string.cancel, null)
                        .show();
            }

            @Override
            public void onError(Throwable error) {
                showError(error);
            }
        });
    }

    private void moveTask(String taskId, Project target) {
        runThenReload(() -> api().moveTask(taskId, target.getId()));
    }

    private void confirmDelete(Task task) {
        new MaterialAlertDialogBuilder(requireContext())
                .setTitle(R.string.task_delete_title)
                .setMessage(getString(R.string.task_delete_message, task.getTitle()))
                .setPositiveButton(R.string.task_delete_confirm, (dialog, which) -> deleteTask(task.getId()))
                .setNegativeButton(android.R.string.cancel, null)
                .show();
    }

    /** Deletes the task, then offers Undo (the only way back: deleted tasks cannot be listed). */
    private void deleteTask(String taskId) {
        async(() -> {
            api().deleteTask(taskId);
            return taskId;
        }, new Async.Callback<String>() {
            @Override
            public void onSuccess(String deletedId) {
                loadBoard();
                View root = getView();
                if (root != null) {
                    Snackbars.undo(root, getString(R.string.task_deleted), () ->
                            runThenReload(() -> api().restoreTask(deletedId)));
                }
            }

            @Override
            public void onError(Throwable error) {
                showError(error);
            }
        });
    }

    /** Opens the form for {@code task}, or a blank one for a new task. */
    private void showEditor(@Nullable Task task) {
        TaskEditDialog.show(this, task, draft -> {
            if (task == null) {
                createTask(draft);
            } else {
                saveChanges(task, draft);
            }
        });
    }

    private void createTask(TaskDraft draft) {
        String projectId = getProjectId();
        Priority priority = draft.priorityOrDefault();
        async(() -> api().createTask(
                projectId,
                draft.trimmedTitle(),
                priority,
                draft.dueDate(),
                draft.descriptionOrNull()), new Async.Callback<Task>() {
            @Override
            public void onSuccess(Task created) {
                // The backend always creates tasks in To do: show that column.
                pager.setCurrentItem(TODO_PAGE, true);
                loadBoard();
            }

            @Override
            public void onError(Throwable error) {
                showError(error);
            }
        });
    }

    /** Sends only the fields that changed; an unchanged form makes no call. */
    private void saveChanges(Task task, TaskDraft draft) {
        TaskPatch patch = draft.changesFrom(task);
        if (patch.isEmpty()) {
            return;
        }
        String taskId = task.getId();
        runThenReload(() -> api().updateTask(taskId, patch));
    }

    /** Runs a server call, then reloads the board; errors are shown. */
    private <T> void runThenReload(Callable<T> work) {
        async(work, new Async.Callback<T>() {
            @Override
            public void onSuccess(T result) {
                loadBoard();
            }

            @Override
            public void onError(Throwable error) {
                showError(error);
            }
        });
    }

    private void setLoading(boolean value) {
        loading = value;
        render();
    }

    /** Pushes the current tasks and loading state into the columns and tab titles. */
    private void render() {
        if (columnAdapter == null) {
            return;
        }
        Map<TaskStatus, List<Task>> columns = TaskColumns.split(tasks);
        columnAdapter.setState(columns, loading);
        for (int i = 0; i < TaskColumns.ORDER.length; i++) {
            TabLayout.Tab tab = tabs.getTabAt(i);
            if (tab != null) {
                tab.setText(tabTitle(i, columns));
            }
        }
    }

    /** Tab label: the column name and how many tasks it holds. */
    private CharSequence tabTitle(int position, Map<TaskStatus, List<Task>> columns) {
        TaskStatus status = TaskColumns.ORDER[position];
        int count = columns.get(status).size();
        return getString(R.string.task_tab_title, getString(TaskColumnPagerAdapter.titleRes(status)), count);
    }

    /** Result of the board load: the project and every task in it. */
    private static final class Board {
        final Project project;
        final List<Task> tasks;

        Board(Project project, List<Task> tasks) {
            this.project = project;
            this.tasks = tasks;
        }
    }
}
