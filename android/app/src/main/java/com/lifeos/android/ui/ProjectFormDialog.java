package com.lifeos.android.ui;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import androidx.annotation.Nullable;
import androidx.annotation.StringRes;
import androidx.appcompat.app.AlertDialog;
import com.google.android.material.dialog.MaterialAlertDialogBuilder;
import com.google.android.material.textfield.TextInputEditText;
import com.google.android.material.textfield.TextInputLayout;
import com.lifeos.android.R;

/** The name and description dialog used to create and to edit a project. */
final class ProjectFormDialog {

    /** Receives the cleaned values: {@code name} is never blank, {@code description} may be null. */
    interface Submit {
        void onSubmit(String name, @Nullable String description);
    }

    private ProjectFormDialog() {}

    /** Shows the dialog prefilled with the given values. The dialog stays open while the name is blank. */
    static void show(Context context, @StringRes int title, String name, String description, Submit submit) {
        View view = LayoutInflater.from(context).inflate(R.layout.dialog_project, null);
        TextInputLayout nameLayout = view.findViewById(R.id.project_name_layout);
        TextInputEditText nameInput = view.findViewById(R.id.project_name_input);
        TextInputEditText descriptionInput = view.findViewById(R.id.project_description_input);
        nameInput.setText(name);
        descriptionInput.setText(description);

        AlertDialog dialog = new MaterialAlertDialogBuilder(context)
                .setTitle(title)
                .setView(view)
                .setNegativeButton(R.string.dialog_cancel, null)
                .setPositiveButton(R.string.save, null)
                .create();
        dialog.setOnShowListener(shown -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            String cleanName = ProjectForm.cleanName(String.valueOf(nameInput.getText()));
            if (cleanName == null) {
                nameLayout.setError(context.getString(R.string.project_name_required));
                return;
            }
            nameLayout.setError(null);
            dialog.dismiss();
            submit.onSubmit(cleanName, ProjectForm.cleanDescription(String.valueOf(descriptionInput.getText())));
        }));
        dialog.show();
    }
}
