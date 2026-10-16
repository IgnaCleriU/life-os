package com.lifeos.android.ui;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import com.lifeos.android.api.model.Project;
import com.lifeos.android.api.model.ProjectStatus;
import com.lifeos.android.api.model.TaskStatus;
import com.lifeos.android.ui.TaskMenu.Action;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import org.junit.Test;

public class TaskMenuTest {

    private static Project project(String id) {
        return new Project(id, "Project " + id, null, ProjectStatus.ACTIVE, Instant.EPOCH);
    }

    @Test
    public void todoOffersStartAndComplete() {
        assertEquals(
                Arrays.asList(Action.START, Action.COMPLETE, Action.EDIT, Action.MOVE, Action.DELETE),
                TaskMenu.actionsFor(TaskStatus.TODO));
    }

    @Test
    public void doingOffersOnlyComplete() {
        assertEquals(
                Arrays.asList(Action.COMPLETE, Action.EDIT, Action.MOVE, Action.DELETE),
                TaskMenu.actionsFor(TaskStatus.DOING));
    }

    @Test
    public void doneOffersOnlyReopen() {
        assertEquals(
                Arrays.asList(Action.REOPEN, Action.EDIT, Action.MOVE, Action.DELETE),
                TaskMenu.actionsFor(TaskStatus.DONE));
    }

    @Test
    public void unknownStatusOffersOnlyTheNonStatusActions() {
        assertEquals(Arrays.asList(Action.EDIT, Action.MOVE, Action.DELETE), TaskMenu.actionsFor(null));
    }

    @Test
    public void moveTargetsExcludeTheCurrentProject() {
        List<Project> targets = TaskMenu.moveTargets(
                Arrays.asList(project("a"), project("b"), project("c")), "b");

        assertEquals(Arrays.asList(project("a").getId(), project("c").getId()), ids(targets));
    }

    @Test
    public void moveTargetsSkipNullEntries() {
        List<Project> targets = TaskMenu.moveTargets(Arrays.asList(null, project("a")), "b");

        assertEquals(List.of("a"), ids(targets));
    }

    @Test
    public void noOtherProjectMeansNoTargets() {
        assertTrue(TaskMenu.moveTargets(List.of(project("only")), "only").isEmpty());
    }

    private static List<String> ids(List<Project> projects) {
        return projects.stream().map(Project::getId).toList();
    }
}
