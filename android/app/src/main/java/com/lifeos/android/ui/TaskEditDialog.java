package com.lifeos.android.ui;

import android.content.Context;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.LayoutInflater;
import android.view.View;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AlertDialog;
import androidx.fragment.app.Fragment;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.datepicker.MaterialDatePicker;
import com.google.android.material.dialog.MaterialAlertDialogBuilder;
import com.google.android.material.textfield.MaterialAutoCompleteTextView;
import com.google.android.material.textfield.TextInputEditText;
import com.google.android.material.textfield.TextInputLayout;
import com.lifeos.android.R;
import com.lifeos.android.api.model.Task;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.time.format.FormatStyle;

/**
 * Create / edit form for a task. Shows a dialog; {@link Listener#onSave} gets the draft only
 * when the title is filled in, and the dialog is closed by then.
 */
final class TaskEditDialog {

    private static final String TAG_DUE_PICKER = "task_due_picker";

    interface Listener {
        void onSave(TaskDraft draft);
    }

    private TaskEditDialog() {}

    /**
     * @param original the task to edit, or null to create one
     */
    static void show(Fragment host, @Nullable Task original, Listener listener) {
        Context context = host.requireContext();
        TaskDraft draft = original == null ? TaskDraft.blank() : TaskDraft.of(original);
        View view = LayoutInflater.from(context).inflate(R.layout.dialog_task, null);

        TextInputLayout titleLayout = view.findViewById(R.id.dialog_task_title_layout);
        TextInputEditText title = view.findViewById(R.id.dialog_task_title);
        TextInputEditText description = view.findViewById(R.id.dialog_task_description);
        MaterialAutoCompleteTextView priority = view.findViewById(R.id.dialog_task_priority);
        TextInputEditText due = view.findViewById(R.id.dialog_task_due);
        MaterialButton clearDue = view.findViewById(R.id.dialog_task_clear_due);

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
            labels[i] = context.getString(TaskPriorities.labelRes(TaskPriorities.ORDER[i]));
        }
        priority.setSimpleItems(labels);
        priority.setText(context.getString(TaskPriorities.labelRes(draft.priorityOrDefault())), false);
        priority.setOnItemClickListener((parent, v, position, id) ->
                draft.setPriority(TaskPriorities.ORDER[position]));

        Runnable showDue = () -> {
            LocalDate date = draft.dueDate();
            due.setText(date == null ? "" : formatDate(date));
            clearDue.setVisibility(date == null ? View.GONE : View.VISIBLE);
        };
        showDue.run();
        due.setOnClickListener(v -> pickDueDate(host, draft, showDue));
        clearDue.setOnClickListener(v -> {
            draft.setDueDate(null);
            showDue.run();
        });

        AlertDialog dialog = new MaterialAlertDialogBuilder(context)
                .setTitle(original == null ? R.string.task_dialog_new_title : R.string.task_dialog_edit_title)
                .setView(view)
                .setPositiveButton(R.string.save, null)
                .setNegativeButton(android.R.string.cancel, null)
                .create();
        // Set the click listener once the dialog shows so a failed validation keeps it open.
        dialog.setOnShowListener(shown -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            draft.setTitle(text(title));
            draft.setDescription(text(description));
            if (!draft.hasTitle()) {
                titleLayout.setError(context.getString(R.string.task_title_required));
                return;
            }
            dialog.dismiss();
            listener.onSave(draft);
        }));
        dialog.show();
    }

    private static void pickDueDate(Fragment host, TaskDraft draft, Runnable onChanged) {
        LocalDate current = draft.dueDate() != null ? draft.dueDate() : LocalDate.now();
        MaterialDatePicker<Long> picker = MaterialDatePicker.Builder.datePicker()
                .setTitleText(R.string.task_field_due)
                .setSelection(TaskDueDates.toUtcMillis(current))
                .build();
        picker.addOnPositiveButtonClickListener(selection -> {
            draft.setDueDate(TaskDueDates.fromUtcMillis(selection));
            onChanged.run();
        });
        picker.show(host.getChildFragmentManager(), TAG_DUE_PICKER);
    }

    private static String formatDate(LocalDate date) {
        return DateTimeFormatter.ofLocalizedDate(FormatStyle.MEDIUM).format(date);
    }

    private static String text(TextInputEditText field) {
        return field.getText() == null ? "" : field.getText().toString();
    }
}
