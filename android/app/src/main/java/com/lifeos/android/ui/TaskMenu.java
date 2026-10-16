package com.lifeos.android.ui;

import com.lifeos.android.api.model.Project;
import com.lifeos.android.api.model.TaskStatus;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * What the action menu of a task offers. Status moves follow the board: a To do task can be
 * started or completed, a Doing task completed, a Done task reopened. Pure Java.
 */
final class TaskMenu {

    enum Action {
        START,
        COMPLETE,
        REOPEN,
        EDIT,
        MOVE,
        DELETE
    }

    private TaskMenu() {}

    /** The actions for a task in {@code status}, status moves first. */
    static List<Action> actionsFor(TaskStatus status) {
        List<Action> actions = new ArrayList<>();
        if (status == TaskStatus.TODO) {
            actions.add(Action.START);
            actions.add(Action.COMPLETE);
        } else if (status == TaskStatus.DOING) {
            actions.add(Action.COMPLETE);
        } else if (status == TaskStatus.DONE) {
            actions.add(Action.REOPEN);
        }
        actions.add(Action.EDIT);
        actions.add(Action.MOVE);
        actions.add(Action.DELETE);
        return actions;
    }

    /** Projects a task can be moved to: active ones, except the project of the board. */
    static List<Project> moveTargets(List<Project> activeProjects, String currentProjectId) {
        List<Project> targets = new ArrayList<>();
        for (Project project : activeProjects) {
            if (project != null && !Objects.equals(project.getId(), currentProjectId)) {
                targets.add(project);
            }
        }
        return targets;
    }
}
