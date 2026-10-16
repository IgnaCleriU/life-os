package com.lifeos.android.ui;

import com.lifeos.android.api.model.ProjectStatus;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/** An action offered from a project row's menu. Pure: the fragment maps each one to a label and a call. */
enum ProjectAction {
    EDIT,
    COMPLETE,
    ARCHIVE,
    ACTIVATE,
    DELETE;

    /** The actions for a project in {@code status}, in menu order. */
    static List<ProjectAction> forStatus(ProjectStatus status) {
        if (status == null) {
            return Arrays.asList(EDIT, DELETE);
        }
        switch (status) {
            case ACTIVE:
                return Arrays.asList(EDIT, COMPLETE, ARCHIVE, DELETE);
            case COMPLETED:
                return Arrays.asList(EDIT, ACTIVATE, ARCHIVE, DELETE);
            case ARCHIVED:
                return Arrays.asList(EDIT, ACTIVATE, DELETE);
            default:
                return Collections.unmodifiableList(Arrays.asList(EDIT, DELETE));
        }
    }
}
