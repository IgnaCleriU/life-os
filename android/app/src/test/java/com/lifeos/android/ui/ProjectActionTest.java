package com.lifeos.android.ui;

import static org.junit.Assert.assertEquals;

import com.lifeos.android.api.model.ProjectStatus;
import java.util.Arrays;
import org.junit.Test;

public class ProjectActionTest {

    @Test
    public void activeProjectCanBeCompletedOrArchived() {
        assertEquals(
                Arrays.asList(ProjectAction.EDIT, ProjectAction.COMPLETE, ProjectAction.ARCHIVE, ProjectAction.DELETE),
                ProjectAction.forStatus(ProjectStatus.ACTIVE));
    }

    @Test
    public void completedProjectCanBeActivatedOrArchived() {
        assertEquals(
                Arrays.asList(ProjectAction.EDIT, ProjectAction.ACTIVATE, ProjectAction.ARCHIVE, ProjectAction.DELETE),
                ProjectAction.forStatus(ProjectStatus.COMPLETED));
    }

    @Test
    public void archivedProjectCanOnlyBeActivated() {
        assertEquals(
                Arrays.asList(ProjectAction.EDIT, ProjectAction.ACTIVATE, ProjectAction.DELETE),
                ProjectAction.forStatus(ProjectStatus.ARCHIVED));
    }

    @Test
    public void unknownStatusOnlyOffersEditAndDelete() {
        assertEquals(Arrays.asList(ProjectAction.EDIT, ProjectAction.DELETE), ProjectAction.forStatus(null));
    }
}
