package com.lifeos.android.util;

import android.content.Context;
import com.lifeos.android.R;
import com.lifeos.android.api.model.ApiException;

/** Maps any failure to one user-facing English sentence (strings live in strings.xml). */
public final class ErrorMessages {

    private ErrorMessages() {}

    public static String of(Context context, Throwable error) {
        if (!(error instanceof ApiException)) {
            String detail = error.getMessage() == null ? error.getClass().getSimpleName() : error.getMessage();
            return context.getString(R.string.error_unexpected, detail);
        }
        ApiException e = (ApiException) error;
        switch (e.getKind()) {
            case NETWORK:
                return context.getString(R.string.error_network);
            case UNAUTHORIZED:
                return context.getString(R.string.error_unauthorized);
            case FORBIDDEN_HOST:
                return context.getString(R.string.error_forbidden_host);
            case FORBIDDEN:
                return context.getString(R.string.error_forbidden);
            case NOT_FOUND:
                return context.getString(R.string.error_not_found);
            case CONFLICT:
                return e.isProjectNotEmpty()
                        ? context.getString(R.string.error_project_not_empty)
                        : context.getString(R.string.error_with_server_message, e.getMessage());
            case VALIDATION:
                return context.getString(R.string.error_with_server_message, e.getMessage());
            case SERVER:
                return context.getString(R.string.error_server, e.getStatus());
            case NOT_CONFIGURED:
                return context.getString(R.string.error_not_configured);
            case OTHER:
            default:
                return context.getString(R.string.error_with_server_message, e.getMessage());
        }
    }

    /** True when fixing the error means opening Settings (bad token, wrong host, nothing configured). */
    public static boolean needsSettings(Throwable error) {
        if (!(error instanceof ApiException)) {
            return false;
        }
        switch (((ApiException) error).getKind()) {
            case UNAUTHORIZED:
            case FORBIDDEN_HOST:
            case NOT_CONFIGURED:
                return true;
            default:
                return false;
        }
    }
}
