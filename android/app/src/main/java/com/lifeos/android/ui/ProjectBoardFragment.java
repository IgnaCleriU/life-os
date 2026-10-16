package com.lifeos.android.ui;

import android.os.Bundle;
import android.view.View;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.viewpager2.widget.ViewPager2;
import com.google.android.material.tabs.TabLayout;
import com.google.android.material.tabs.TabLayoutMediator;
import com.lifeos.android.R;
import com.lifeos.android.api.model.Project;
import com.lifeos.android.api.model.Task;
import com.lifeos.android.api.model.TaskQuery;
import com.lifeos.android.api.model.TaskStatus;
import com.lifeos.android.util.Async;
import java.time.Clock;
import java.util.List;
import java.util.Map;

/**
 * Task board of one project: three swipeable columns (To do / Doing / Done). All tasks are
 * loaded once and split by status here. Open it with {@code Navigator.openProject(id)}.
 */
public class ProjectBoardFragment extends BaseFragment {

    static final String TAG = "project_board";
    private static final String ARG_PROJECT_ID = "project_id";

    private final Clock clock = Clock.systemDefaultZone();

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
                // Task actions are wired in a later step.
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
