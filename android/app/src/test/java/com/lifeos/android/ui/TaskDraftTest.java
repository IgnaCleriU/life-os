package com.lifeos.android.ui;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import com.google.gson.JsonObject;
import com.lifeos.android.api.model.Priority;
import com.lifeos.android.api.model.Task;
import com.lifeos.android.api.model.TaskPatch;
import com.lifeos.android.api.model.TaskStatus;
import java.time.Instant;
import java.time.LocalDate;
import org.junit.Test;

public class TaskDraftTest {

    private static final LocalDate DUE = LocalDate.parse("2026-10-20");

    private static Task original() {
        return new Task("t1", "p1", "Buy milk", "Semi-skimmed", TaskStatus.TODO, Priority.MEDIUM, DUE,
                Instant.EPOCH);
    }

    private static Task withoutDescriptionOrDue() {
        return new Task("t1", "p1", "Buy milk", null, TaskStatus.TODO, Priority.MEDIUM, null, Instant.EPOCH);
    }

    @Test
    public void blankFormHasNoTitleAndMediumPriority() {
        TaskDraft draft = TaskDraft.blank();

        assertFalse(draft.hasTitle());
        assertEquals(Priority.MEDIUM, draft.priorityOrDefault());
        assertNull(draft.dueDate());
        assertNull(draft.descriptionOrNull());
    }

    @Test
    public void whitespaceOnlyTitleIsRejected() {
        TaskDraft draft = TaskDraft.blank();
        draft.setTitle("   \t ");

        assertFalse(draft.hasTitle());
    }

    @Test
    public void titleAndDescriptionAreTrimmed() {
        TaskDraft draft = TaskDraft.blank();
        draft.setTitle("  Ship it  ");
        draft.setDescription("  notes \n");

        assertEquals("Ship it", draft.trimmedTitle());
        assertEquals("notes", draft.descriptionOrNull());
    }

    @Test
    public void unchangedFormProducesEmptyPatch() {
        TaskDraft draft = TaskDraft.of(original());

        assertTrue(draft.changesFrom(original()).isEmpty());
    }

    @Test
    public void whitespaceOnlyEditsDoNotCountAsChanges() {
        TaskDraft draft = TaskDraft.of(original());
        draft.setTitle("  Buy milk ");
        draft.setDescription(" Semi-skimmed  ");

        assertTrue(draft.changesFrom(original()).isEmpty());
    }

    @Test
    public void onlyTheChangedTitleIsSent() {
        TaskDraft draft = TaskDraft.of(original());
        draft.setTitle("Buy oat milk");

        JsonObject json = draft.changesFrom(original()).toJson();

        assertEquals(1, json.size());
        assertEquals("Buy oat milk", json.get("title").getAsString());
    }

    @Test
    public void clearingTheDescriptionSendsExplicitNull() {
        TaskDraft draft = TaskDraft.of(original());
        draft.setDescription("   ");

        JsonObject json = draft.changesFrom(original()).toJson();

        assertTrue(json.has("description"));
        assertTrue(json.get("description").isJsonNull());
    }

    @Test
    public void addingADescriptionSendsIt() {
        Task plain = withoutDescriptionOrDue();
        TaskDraft draft = TaskDraft.of(plain);
        draft.setDescription("Two litres");

        JsonObject json = draft.changesFrom(plain).toJson();

        assertEquals("Two litres", json.get("description").getAsString());
        assertEquals(1, json.size());
    }

    @Test
    public void clearingTheDueDateSendsExplicitNull() {
        TaskDraft draft = TaskDraft.of(original());
        draft.setDueDate(null);

        JsonObject json = draft.changesFrom(original()).toJson();

        assertTrue(json.get("due_date").isJsonNull());
    }

    @Test
    public void settingADueDateSendsIsoDate() {
        Task plain = withoutDescriptionOrDue();
        TaskDraft draft = TaskDraft.of(plain);
        draft.setDueDate(DUE);

        JsonObject json = draft.changesFrom(plain).toJson();

        assertEquals("2026-10-20", json.get("due_date").getAsString());
        assertEquals(1, json.size());
    }

    @Test
    public void changedPrioritySendsItsWireValue() {
        TaskDraft draft = TaskDraft.of(original());
        draft.setPriority(Priority.HIGH);

        TaskPatch patch = draft.changesFrom(original());

        assertEquals("high", patch.toJson().get("priority").getAsString());
        assertEquals(1, patch.toJson().size());
    }

    @Test
    public void taskWithoutPriorityIsNotPatchedUntilChosen() {
        Task noPriority = new Task("t1", "p1", "Buy milk", null, TaskStatus.TODO, null, null, Instant.EPOCH);
        TaskDraft draft = TaskDraft.of(noPriority);

        assertTrue(draft.changesFrom(noPriority).isEmpty());
    }

    @Test
    public void stateRoundTripKeepsEveryField() {
        TaskDraft draft = TaskDraft.of(original());
        draft.setTitle("  Edited ");
        draft.setPriority(Priority.HIGH);

        TaskDraft restored = TaskDraft.fromState(
                draft.getTitle(), draft.getDescription(), draft.priorityName(), draft.dueEpochDay());

        assertEquals("  Edited ", restored.getTitle());
        assertEquals("Semi-skimmed", restored.getDescription());
        assertEquals(Priority.HIGH, restored.priorityOrDefault());
        assertEquals(DUE, restored.dueDate());
    }

    @Test
    public void stateRoundTripKeepsMissingPriorityAndDueAsNull() {
        Task noPriority = new Task("t1", "p1", "Buy milk", null, TaskStatus.TODO, null, null, Instant.EPOCH);
        TaskDraft draft = TaskDraft.of(noPriority);

        TaskDraft restored = TaskDraft.fromState(
                draft.getTitle(), draft.getDescription(), draft.priorityName(), draft.dueEpochDay());

        assertNull(draft.priorityName());
        assertNull(restored.dueDate());
        assertTrue(restored.changesFrom(noPriority).isEmpty());
    }

    @Test
    public void restoredDraftKeepsPatchSemantics() {
        TaskDraft draft = TaskDraft.of(original());
        draft.setDueDate(null);
        TaskDraft restored = TaskDraft.fromState(
                draft.getTitle(), draft.getDescription(), draft.priorityName(), draft.dueEpochDay());

        TaskPatch patch = restored.changesFrom(original());

        assertFalse(patch.isEmpty());
        assertTrue(TaskDraft.of(original()).changesFrom(original()).isEmpty());
    }

    @Test
    public void changesAreDiffedAgainstTheValuesTheFormWasOpenedWith() {
        TaskDraft opened = TaskDraft.of(original());
        TaskDraft draft = TaskDraft.of(original());
        draft.setTitle("Buy oat milk");
        // Someone else changed the description meanwhile: the draft never touched it, so it is not sent.
        JsonObject json = draft.changesFrom(opened).toJson();
        assertEquals("Buy oat milk", json.get("title").getAsString());
        assertFalse(json.has("description"));
        assertTrue(TaskDraft.of(original()).changesFrom(opened).isEmpty());
    }
}
