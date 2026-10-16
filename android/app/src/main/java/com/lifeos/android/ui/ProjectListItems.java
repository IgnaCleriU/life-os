package com.lifeos.android.ui;

import com.lifeos.android.api.model.Project;
import com.lifeos.android.api.model.ProjectStatus;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

/**
 * Turns a flat project list into the rows the Projects screen shows: a header
 * per status section (Active, Completed, Archived, in that order; empty sections
 * are left out) followed by the projects of that section, sorted by name.
 *
 * <p>Pure Java with no Android types, so it is unit tested. Projects whose status
 * this app does not know have no section and are left out.
 */
final class ProjectListItems {

    /** Display order of the sections. */
    static final List<ProjectStatus> SECTION_ORDER = Collections.unmodifiableList(
            Arrays.asList(ProjectStatus.ACTIVE, ProjectStatus.COMPLETED, ProjectStatus.ARCHIVED));

    private static final Comparator<Project> BY_NAME =
            Comparator.comparing(Project::getName, Comparator.nullsLast(String.CASE_INSENSITIVE_ORDER));

    private ProjectListItems() {}

    /** The rows, in display order. */
    static List<Item> build(List<Project> projects) {
        List<Item> items = new ArrayList<>();
        for (ProjectStatus section : SECTION_ORDER) {
            List<Project> group = new ArrayList<>();
            for (Project project : projects) {
                if (project != null && project.getStatus() == section) {
                    group.add(project);
                }
            }
            if (group.isEmpty()) {
                continue;
            }
            group.sort(BY_NAME);
            items.add(Item.header(section));
            for (Project project : group) {
                items.add(Item.project(project));
            }
        }
        return items;
    }

    /** A section header ({@link #isHeader()}) or a project row. */
    static final class Item {
        private final boolean header;
        private final ProjectStatus status;
        private final Project project;

        private Item(boolean header, ProjectStatus status, Project project) {
            this.header = header;
            this.status = status;
            this.project = project;
        }

        static Item header(ProjectStatus section) {
            return new Item(true, section, null);
        }

        static Item project(Project project) {
            return new Item(false, project.getStatus(), project);
        }

        boolean isHeader() {
            return header;
        }

        /** The section this row belongs to (the header's section, or the project's status). */
        ProjectStatus getStatus() {
            return status;
        }

        /** Null for a header. */
        Project getProject() {
            return project;
        }
    }
}
