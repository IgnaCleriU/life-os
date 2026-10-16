package com.lifeos.android.ui;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import com.lifeos.android.api.model.Project;
import com.lifeos.android.api.model.ProjectStatus;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import org.junit.Test;

public class ProjectListItemsTest {

    private static Project project(String name, ProjectStatus status) {
        return new Project("id-" + name, name, null, status, null);
    }

    @Test
    public void emptyInputGivesNoRows() {
        assertTrue(ProjectListItems.build(Collections.emptyList()).isEmpty());
    }

    @Test
    public void sectionsAreInStatusOrderWithAHeaderEach() {
        List<ProjectListItems.Item> items = ProjectListItems.build(Arrays.asList(
                project("Old", ProjectStatus.ARCHIVED),
                project("Done", ProjectStatus.COMPLETED),
                project("Now", ProjectStatus.ACTIVE)));

        assertEquals(6, items.size());
        assertHeader(items.get(0), ProjectStatus.ACTIVE);
        assertEquals("Now", items.get(1).getProject().getName());
        assertHeader(items.get(2), ProjectStatus.COMPLETED);
        assertEquals("Done", items.get(3).getProject().getName());
        assertHeader(items.get(4), ProjectStatus.ARCHIVED);
        assertEquals("Old", items.get(5).getProject().getName());
    }

    @Test
    public void emptySectionsGetNoHeader() {
        List<ProjectListItems.Item> items = ProjectListItems.build(Arrays.asList(
                project("Only", ProjectStatus.ACTIVE)));

        assertEquals(2, items.size());
        assertHeader(items.get(0), ProjectStatus.ACTIVE);
        assertFalse(items.get(1).isHeader());
    }

    @Test
    public void projectsInASectionAreSortedByNameIgnoringCase() {
        List<ProjectListItems.Item> items = ProjectListItems.build(Arrays.asList(
                project("beta", ProjectStatus.ACTIVE),
                project("Alpha", ProjectStatus.ACTIVE),
                project("gamma", ProjectStatus.ACTIVE)));

        assertEquals("Alpha", items.get(1).getProject().getName());
        assertEquals("beta", items.get(2).getProject().getName());
        assertEquals("gamma", items.get(3).getProject().getName());
    }

    @Test
    public void unknownStatusAndNullEntriesAreLeftOut() {
        List<ProjectListItems.Item> items = ProjectListItems.build(Arrays.asList(
                project("Mystery", null),
                null,
                project("Real", ProjectStatus.ACTIVE)));

        assertEquals(2, items.size());
        assertEquals("Real", items.get(1).getProject().getName());
    }

    @Test
    public void headerHasNoProject() {
        ProjectListItems.Item header = ProjectListItems.build(Collections.singletonList(
                project("A", ProjectStatus.ACTIVE))).get(0);

        assertTrue(header.isHeader());
        assertNull(header.getProject());
    }

    private static void assertHeader(ProjectListItems.Item item, ProjectStatus section) {
        assertTrue(item.isHeader());
        assertEquals(section, item.getStatus());
    }
}
