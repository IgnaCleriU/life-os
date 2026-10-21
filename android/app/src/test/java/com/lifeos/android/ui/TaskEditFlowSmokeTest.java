package com.lifeos.android.ui;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import android.app.Dialog;
import android.widget.TextView;
import androidx.appcompat.app.AlertDialog;
import androidx.fragment.app.FragmentFactory;
import androidx.fragment.app.FragmentManager;
import androidx.fragment.app.testing.FragmentScenario;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.lifeos.android.R;
import com.lifeos.android.TestApp;
import com.lifeos.android.api.model.Priority;
import com.lifeos.android.api.model.Task;
import com.lifeos.android.api.model.TaskStatus;
import java.time.Instant;
import java.time.LocalDate;
import okhttp3.mockwebserver.RecordedRequest;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

/**
 * Saves the real task form on the real board and checks what reaches the API. The diff logic
 * has unit tests in TaskDraftTest; these cover the wiring between the form, its result and the
 * board: the patch must be diffed against the values the form was opened with.
 */
@RunWith(RobolectricTestRunner.class)
@Config(application = TestApp.class, sdk = 35)
public class TaskEditFlowSmokeTest {

    private FakeApi api;

    @Before
    public void setUp() throws Exception {
        api = new FakeApi();
        TestApp.baseUrl = api.baseUrl();
    }

    @After
    public void tearDown() throws Exception {
        api.shutdown();
    }

    private FragmentScenario<ProjectBoardFragment> launch() {
        return FragmentScenario.launchInContainer(
                ProjectBoardFragment.class,
                ProjectBoardFragment.newInstance(FakeApi.PROJECT_ID).getArguments(),
                R.style.Theme_LifeOs,
                (FragmentFactory) null);
    }

    /** What the user saw when opening the form. The server holds different details by now. */
    private static Task opened(String id) {
        return new Task(id, FakeApi.PROJECT_ID, "Fix tap", "Old details", TaskStatus.TODO, Priority.HIGH,
                LocalDate.parse("2020-01-01"), Instant.EPOCH);
    }

    /** Opens the form for {@code task}, types {@code newTitle} (if not null) and presses Save. */
    private static void editAndSave(ProjectBoardFragment board, Task task, String newTitle) {
        FragmentManager children = board.getChildFragmentManager();
        TaskEditDialog.newInstance(task, FakeApi.PROJECT_ID).show(children, TaskEditDialog.TAG);
        children.executePendingTransactions();
        // The dialog announces itself (and the Save listener gets attached) through a handler.
        org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();
        TaskEditDialog form = (TaskEditDialog) children.findFragmentByTag(TaskEditDialog.TAG);
        assertNotNull(form);
        Dialog dialog = form.getDialog();
        assertNotNull(dialog);
        if (newTitle != null) {
            ((TextView) dialog.findViewById(R.id.dialog_task_title)).setText(newTitle);
        }
        ((AlertDialog) dialog).getButton(AlertDialog.BUTTON_POSITIVE).performClick();
    }

    private static void awaitBoard(ProjectBoardFragment board) {
        UiTestSupport.waitFor("board loaded", () -> board.getView() != null
                && board.getView().findViewById(R.id.task_board_tabs) != null
                && ((com.google.android.material.tabs.TabLayout) board.getView()
                        .findViewById(R.id.task_board_tabs)).getTabAt(0) != null
                && String.valueOf(((com.google.android.material.tabs.TabLayout) board.getView()
                        .findViewById(R.id.task_board_tabs)).getTabAt(0).getText()).contains("2"));
    }

    @Test
    public void onlyTheEditedFieldIsSentEvenIfTheServerCopyDiffers() {
        try (FragmentScenario<ProjectBoardFragment> scenario = launch()) {
            scenario.onFragment(board -> {
                awaitBoard(board);
                editAndSave(board, opened("t1"), "Fix the tap");
                UiTestSupport.waitFor("patch sent", () -> !api.patches().isEmpty());
            });
        }

        assertEquals(1, api.patches().size());
        RecordedRequest patch = api.patches().get(0);
        assertEquals("/tasks/t1", patch.getPath());
        JsonObject body = JsonParser.parseString(patch.getBody().readUtf8()).getAsJsonObject();
        assertEquals("Fix the tap", body.get("title").getAsString());
        // Diffed against the cache ("Details" on the server) this would also send the
        // description the user never touched, overwriting another client's edit.
        assertEquals(1, body.size());
    }

    @Test
    public void unchangedFormMakesNoUpdateCall() {
        try (FragmentScenario<ProjectBoardFragment> scenario = launch()) {
            scenario.onFragment(board -> {
                awaitBoard(board);
                editAndSave(board, opened("t1"), null);
                // Let any (wrongly) queued call run before looking.
                for (int i = 0; i < 20; i++) {
                    org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();
                }
            });
        }

        assertTrue(api.patches().isEmpty());
    }

    @Test
    public void savingATaskDeletedElsewhereIsReportedNotDropped() {
        try (FragmentScenario<ProjectBoardFragment> scenario = launch()) {
            scenario.onFragment(board -> {
                awaitBoard(board);
                editAndSave(board, opened(FakeApi.GONE_TASK_ID), "Anything");
                UiTestSupport.waitFor("patch sent", () -> !api.patches().isEmpty());
            });
        }

        // The edit reaches the server (which answers 404) even though the task is not in the
        // board's cache.
        assertEquals("/tasks/" + FakeApi.GONE_TASK_ID, api.patches().get(0).getPath());
    }
}
