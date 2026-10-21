package com.lifeos.android.ui;

import android.app.Dialog;
import android.content.Context;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.LayoutInflater;
import android.view.View;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AlertDialog;
import androidx.fragment.app.DialogFragment;
import androidx.fragment.app.Fragment;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.datepicker.MaterialDatePicker;
import com.google.android.material.dialog.MaterialAlertDialogBuilder;
import com.google.android.material.textfield.MaterialAutoCompleteTextView;
import com.google.android.material.textfield.TextInputEditText;
import com.google.android.material.textfield.TextInputLayout;
import com.lifeos.android.R;
import com.lifeos.android.api.model.Task;
import java.time.Clock;
import java.time.LocalDate;

/**
 * Create / edit form for a task, as a DialogFragment so it (and its date picker) survive
 * rotation. The draft is kept in the saved state. On save the draft goes to the parent
 * FragmentManager as a fragment result under {@link #REQUEST_KEY}; read it with
 * {@link #draftFrom(Bundle)}, {@link #originalFrom(Bundle)} and {@link #taskIdFrom(Bundle)} (null id means a new task).
 * The title is required: nothing is sent while it is blank.
 */
public final class TaskEditDialog extends DialogFragment {

    static final String TAG = "task_edit";
    static final String REQUEST_KEY = "task_edit_result";

    private static final String TAG_DUE_PICKER = "task_due_picker";
    private static final String ARG_TASK_ID = "task_id";
    private static final String ARG_PROJECT_ID = "project_id";
    private static final String PREFIX_DRAFT = "draft_";
    /** Values the form was opened with; the save diffs against them, not against a cache. */
    private static final String PREFIX_ORIGINAL = "original_";
    private static final String KEY_TITLE = "draft_title";

    /** Implemented by the parent fragment so "today" comes from its (injectable) clock. */
    interface Host {
        Clock clock();
    }

    private TaskDraft draft;

    private TextInputLayout titleLayout;
    private TextInputEditText title;
    private TextInputEditText description;
    private TextInputEditText due;
    private MaterialButton clearDue;

    /** Required by the framework; use {@link #newInstance}. */
    public TaskEditDialog() {}

    /**
     * @param original the task to edit, or null to create one in {@code projectId}
     */
    static TaskEditDialog newInstance(@Nullable Task original, String projectId) {
        TaskEditDialog dialog = new TaskEditDialog();
        Bundle args = new Bundle();
        args.putString(ARG_PROJECT_ID, projectId);
        if (original != null) {
            args.putString(ARG_TASK_ID, original.getId());
        }
        TaskDraft opened = original == null ? TaskDraft.blank() : TaskDraft.of(original);
        writeDraft(args, PREFIX_DRAFT, opened);
        writeDraft(args, PREFIX_ORIGINAL, opened);
        dialog.setArguments(args);
        return dialog;
    }

    /** The draft in a result (or saved state / arguments) bundle. */
    static TaskDraft draftFrom(Bundle bundle) {
        return readDraft(bundle, PREFIX_DRAFT);
    }

    /** The values the task had when the form was opened (what the user saw and edited). */
    static TaskDraft originalFrom(Bundle bundle) {
        return readDraft(bundle, PREFIX_ORIGINAL);
    }

    private static TaskDraft readDraft(Bundle bundle, String prefix) {
        return TaskDraft.fromState(
                bundle.getString(prefix + "title"),
                bundle.getString(prefix + "description"),
                bundle.getString(prefix + "priority"),
                bundle.containsKey(prefix + "due") ? bundle.getLong(prefix + "due") : null);
    }

    /** The id of the task that was edited, or null when the form created a new one. */
    @Nullable
    static String taskIdFrom(Bundle result) {
        return result.getString(ARG_TASK_ID);
    }

    private static void writeDraft(Bundle bundle, String prefix, TaskDraft draft) {
        bundle.putString(prefix + "title", draft.getTitle());
        bundle.putString(prefix + "description", draft.getDescription());
        bundle.putString(prefix + "priority", draft.priorityName());
        Long dueDay = draft.dueEpochDay();
        if (dueDay != null) {
            bundle.putLong(prefix + "due", dueDay);
        }
    }

    @Override
    public void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        boolean restored = savedInstanceState != null && savedInstanceState.containsKey(KEY_TITLE);
        draft = draftFrom(restored ? savedInstanceState : requireArguments());
    }

    @NonNull
    @Override
    public Dialog onCreateDialog(@Nullable Bundle savedInstanceState) {
        Context context = requireContext();
        boolean isNew = requireArguments().getString(ARG_TASK_ID) == null;
        View view = LayoutInflater.from(context).inflate(R.layout.dialog_task, null);

        titleLayout = view.findViewById(R.id.dialog_task_title_layout);
        title = view.findViewById(R.id.dialog_task_title);
        description = view.findViewById(R.id.dialog_task_description);
        MaterialAutoCompleteTextView priority = view.findViewById(R.id.dialog_task_priority);
        due = view.findViewById(R.id.dialog_task_due);
        clearDue = view.findViewById(R.id.dialog_task_clear_due);

        title.setText(draft.getTitle());
        title.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                titleLayout.setError(null);
            }

            @Override
            public void afterTextChanged(Editable s) {}
        });
        description.setText(draft.getDescription());

        String[] labels = new String[TaskPriorities.ORDER.length];
        for (int i = 0; i < labels.length; i++) {
            labels[i] = getString(TaskPriorities.labelRes(TaskPriorities.ORDER[i]));
        }
        priority.setSimpleItems(labels);
        priority.setText(getString(TaskPriorities.labelRes(draft.priorityOrDefault())), false);
        priority.setOnItemClickListener((parent, v, position, id) ->
                draft.setPriority(TaskPriorities.ORDER[position]));

        showDue();
        due.setOnClickListener(v -> pickDueDate());
        clearDue.setOnClickListener(v -> {
            draft.setDueDate(null);
            showDue();
        });
        // After a rotation the picker fragment is restored by the FragmentManager, but its
        // listeners are not: attach ours again.
        Fragment restoredPicker = getChildFragmentManager().findFragmentByTag(TAG_DUE_PICKER);
        if (restoredPicker instanceof MaterialDatePicker) {
            listenTo((MaterialDatePicker<?>) restoredPicker);
        }

        AlertDialog dialog = new MaterialAlertDialogBuilder(context)
                .setTitle(isNew ? R.string.task_dialog_new_title : R.string.task_dialog_edit_title)
                .setView(view)
                .setPositiveButton(R.string.save, null)
                .setNegativeButton(android.R.string.cancel, null)
                .create();
        // Set the click listener once the dialog shows so a failed validation keeps it open.
        dialog.setOnShowListener(shown ->
                dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> save()));
        return dialog;
    }

    @Override
    public void onSaveInstanceState(@NonNull Bundle outState) {
        super.onSaveInstanceState(outState);
        syncDraftFromFields();
        writeDraft(outState, PREFIX_DRAFT, draft);
    }

    @Override
    public void onDestroyView() {
        titleLayout = null;
        title = null;
        description = null;
        due = null;
        clearDue = null;
        super.onDestroyView();
    }

    /** Copies what the user typed into the draft (priority and date are written as they change). */
    private void syncDraftFromFields() {
        if (title != null) {
            draft.setTitle(text(title));
        }
        if (description != null) {
            draft.setDescription(text(description));
        }
    }

    private void save() {
        syncDraftFromFields();
        if (!draft.hasTitle()) {
            titleLayout.setError(getString(R.string.task_title_required));
            return;
        }
        Bundle result = new Bundle();
        writeDraft(result, PREFIX_DRAFT, draft);
        writeDraft(result, PREFIX_ORIGINAL, originalFrom(requireArguments()));
        result.putString(ARG_TASK_ID, requireArguments().getString(ARG_TASK_ID));
        getParentFragmentManager().setFragmentResult(REQUEST_KEY, result);
        dismiss();
    }

    private void showDue() {
        LocalDate date = draft.dueDate();
        due.setText(date == null ? "" : TaskDueDates.format(date));
        clearDue.setVisibility(date == null ? View.GONE : View.VISIBLE);
    }

    private void pickDueDate() {
        LocalDate today = LocalDate.now(clock());
        LocalDate current = draft.dueDate() != null ? draft.dueDate() : today;
        MaterialDatePicker<Long> picker = MaterialDatePicker.Builder.datePicker()
                .setTitleText(R.string.task_field_due)
                .setSelection(TaskDueDates.toUtcMillis(current))
                .build();
        listenTo(picker);
        picker.show(getChildFragmentManager(), TAG_DUE_PICKER);
    }

    @SuppressWarnings("unchecked")
    private void listenTo(MaterialDatePicker<?> picker) {
        ((MaterialDatePicker<Long>) picker).addOnPositiveButtonClickListener(selection -> {
            draft.setDueDate(TaskDueDates.fromUtcMillis(selection));
            if (due != null) {
                showDue();
            }
        });
    }

    private Clock clock() {
        Fragment parent = getParentFragment();
        return parent instanceof Host ? ((Host) parent).clock() : Clock.systemDefaultZone();
    }

    private static String text(TextInputEditText field) {
        return field.getText() == null ? "" : field.getText().toString();
    }
}
