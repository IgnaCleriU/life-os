package com.lifeos.android.ui;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import com.lifeos.android.api.model.Project;
import com.lifeos.android.api.model.ProjectPatch;
import com.lifeos.android.api.model.ProjectStatus;
import org.junit.Test;

public class ProjectFormTest {

    private static Project original(String name, String description) {
        return new Project("id", name, description, ProjectStatus.ACTIVE, null);
    }

    @Test
    public void blankNameIsRejectedAndNamesAreTrimmed() {
        assertNull(ProjectForm.cleanName("   "));
        assertNull(ProjectForm.cleanName(null));
        assertEquals("Garden", ProjectForm.cleanName("  Garden \n"));
    }

    @Test
    public void blankDescriptionMeansNoDescription() {
        assertNull(ProjectForm.cleanDescription(""));
        assertNull(ProjectForm.cleanDescription(" \t "));
        assertEquals("Spring plants", ProjectForm.cleanDescription(" Spring plants "));
    }

    @Test
    public void noChangesGivesNoPatch() {
        assertNull(ProjectForm.changes(original("Garden", "Beds"), "Garden", "Beds"));
        assertNull(ProjectForm.changes(original("Garden", "  Beds "), " Garden ", "Beds"));
    }

    @Test
    public void nothingToClearWhenBothDescriptionsAreBlank() {
        assertNull(ProjectForm.changes(original("Garden", null), "Garden", "   "));
        assertNull(ProjectForm.changes(original("Garden", "  "), "Garden", ""));
    }

    @Test
    public void sendsOnlyTheChangedName() {
        ProjectPatch patch = ProjectForm.changes(original("Garden", "Beds"), "Garden 2", "Beds");

        assertEquals(1, patch.toJson().size());
        assertEquals("Garden 2", patch.toJson().get("name").getAsString());
    }

    @Test
    public void sendsOnlyTheChangedDescription() {
        ProjectPatch patch = ProjectForm.changes(original("Garden", "Beds"), "Garden", "Pots");

        assertEquals(1, patch.toJson().size());
        assertEquals("Pots", patch.toJson().get("description").getAsString());
    }

    @Test
    public void clearedDescriptionIsSentAsExplicitNull() {
        ProjectPatch patch = ProjectForm.changes(original("Garden", "Beds"), "Garden", "");

        assertTrue(patch.toJson().has("description"));
        assertTrue(patch.toJson().get("description").isJsonNull());
        assertEquals(1, patch.toJson().size());
    }

    @Test
    public void addingADescriptionToAProjectWithoutOneIsAChange() {
        ProjectPatch patch = ProjectForm.changes(original("Garden", null), "Garden", "Beds");

        assertEquals("Beds", patch.toJson().get("description").getAsString());
    }
}
