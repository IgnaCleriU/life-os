package com.lifeos.android.ui;

import com.lifeos.android.api.model.Project;
import com.lifeos.android.api.model.ProjectPatch;
import java.util.Objects;

/**
 * Rules shared by the create and edit dialogs: names and descriptions are trimmed,
 * a blank description means "no description", and an edit sends only what changed.
 * Pure Java so it is unit tested.
 */
final class ProjectForm {

    private ProjectForm() {}

    /** The trimmed name, or null if it is blank (the name is required). */
    static String cleanName(String input) {
        return blankToNull(input);
    }

    /** The trimmed description, or null if it is blank. */
    static String cleanDescription(String input) {
        return blankToNull(input);
    }

    /**
     * The changes that turn {@code original} into the entered values, or null when nothing
     * changed. A description that was cleared is sent as an explicit null.
     */
    static ProjectPatch changes(Project original, String name, String description) {
        ProjectPatch patch = new ProjectPatch();
        String newName = cleanName(name);
        if (newName != null && !newName.equals(original.getName())) {
            patch.name(newName);
        }
        String newDescription = cleanDescription(description);
        if (!Objects.equals(newDescription, cleanDescription(original.getDescription()))) {
            if (newDescription == null) {
                patch.clearDescription();
            } else {
                patch.description(newDescription);
            }
        }
        return patch.isEmpty() ? null : patch;
    }

    private static String blankToNull(String input) {
        if (input == null) {
            return null;
        }
        String trimmed = input.trim();
        return trimmed.isEmpty() ? null : trimmed;
    }
}
