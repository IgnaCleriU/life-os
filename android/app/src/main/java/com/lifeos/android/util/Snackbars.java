package com.lifeos.android.util;

import android.view.View;
import com.google.android.material.snackbar.Snackbar;
import com.lifeos.android.R;

/** Snackbar helpers shared by every screen. Call from the main thread. */
public final class Snackbars {

    /** Long enough to notice and tap Undo, which is the only way back after a delete. */
    private static final int UNDO_DURATION_MS = 8000;

    private Snackbars() {}

    /**
     * Shows {@code message} with an "Undo" action that runs {@code onUndo}. Use it after
     * a delete (the backend has no list of deleted items, so restore is only possible
     * right now): delete first, then offer {@code () -> api.restoreTask(id)}.
     */
    public static Snackbar undo(View anchor, CharSequence message, Runnable onUndo) {
        Snackbar bar = Snackbar.make(anchor, message, UNDO_DURATION_MS)
                .setAction(R.string.undo, v -> onUndo.run());
        bar.show();
        return bar;
    }

    /** Shows a plain message. */
    public static Snackbar info(View anchor, CharSequence message) {
        Snackbar bar = Snackbar.make(anchor, message, Snackbar.LENGTH_SHORT);
        bar.show();
        return bar;
    }

    /** Shows {@link ErrorMessages#of} for {@code error}. */
    public static Snackbar error(View anchor, Throwable error) {
        Snackbar bar = Snackbar.make(anchor, ErrorMessages.of(anchor.getContext(), error), Snackbar.LENGTH_LONG);
        bar.show();
        return bar;
    }

    /** Like {@link #error} but with a Settings action, for errors where {@link ErrorMessages#needsSettings} holds. */
    public static Snackbar errorWithSettings(View anchor, Throwable error, Runnable openSettings) {
        Snackbar bar = Snackbar.make(anchor, ErrorMessages.of(anchor.getContext(), error), Snackbar.LENGTH_LONG)
                .setAction(R.string.settings, v -> openSettings.run());
        bar.show();
        return bar;
    }
}
