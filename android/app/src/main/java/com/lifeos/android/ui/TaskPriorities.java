package com.lifeos.android.ui;

import androidx.annotation.StringRes;
import com.lifeos.android.R;
import com.lifeos.android.api.model.Priority;

/** Display order and labels of task priorities, shared by the cards and the edit form. */
final class TaskPriorities {

    /** Order of the priority dropdown: lowest first. */
    static final Priority[] ORDER = {Priority.LOW, Priority.MEDIUM, Priority.HIGH};

    private TaskPriorities() {}

    /** The label of a priority, looked up explicitly (not by enum position). */
    static @StringRes int labelRes(Priority priority) {
        switch (priority) {
            case HIGH:
                return R.string.task_priority_high;
            case MEDIUM:
                return R.string.task_priority_medium;
            case LOW:
            default:
                return R.string.task_priority_low;
        }
    }
}
