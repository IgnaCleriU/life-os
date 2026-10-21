package com.lifeos.android.ui;

import androidx.annotation.Nullable;
import androidx.lifecycle.ViewModel;
import com.lifeos.android.api.model.Task;
import java.util.List;

/**
 * State of one project board. It outlives the fragment's view (rotation), so the board can draw
 * the previous data straight away while a refresh runs.
 */
public final class ProjectBoardViewModel extends ViewModel {

    private List<Task> tasks = List.of();
    private String projectName;
    private boolean loading;

    List<Task> getTasks() {
        return tasks;
    }

    @Nullable
    String getProjectName() {
        return projectName;
    }

    boolean isLoading() {
        return loading;
    }

    void setTasks(List<Task> tasks) {
        this.tasks = tasks;
    }

    void setProjectName(@Nullable String projectName) {
        this.projectName = projectName;
    }

    void setLoading(boolean loading) {
        this.loading = loading;
    }
}
