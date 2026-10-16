package com.lifeos.android.ui;

import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.annotation.StringRes;
import com.google.android.material.textfield.TextInputEditText;
import com.google.android.material.textfield.TextInputLayout;
import com.lifeos.android.R;
import com.lifeos.android.api.ApiClient;
import com.lifeos.android.api.ConnectionCheck;
import com.lifeos.android.settings.BaseUrl;
import com.lifeos.android.settings.SettingsStore;
import com.lifeos.android.util.Snackbars;
import java.security.GeneralSecurityException;

/** API base URL + token, with a "Test connection" probe. */
public class SettingsFragment extends BaseFragment {

    static final String TAG = "settings";

    private TextInputLayout urlLayout;
    private TextInputEditText urlInput;
    private TextInputLayout tokenLayout;
    private TextInputEditText tokenInput;
    private Button testButton;
    private Button saveButton;
    private ProgressBar progress;
    private TextView result;

    public SettingsFragment() {
        super(R.layout.fragment_settings);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        urlLayout = view.findViewById(R.id.url_layout);
        urlInput = view.findViewById(R.id.url_input);
        tokenLayout = view.findViewById(R.id.token_layout);
        tokenInput = view.findViewById(R.id.token_input);
        testButton = view.findViewById(R.id.test_button);
        saveButton = view.findViewById(R.id.save_button);
        progress = view.findViewById(R.id.progress);
        result = view.findViewById(R.id.result);

        SettingsStore store = app().settings();
        if (savedInstanceState == null) {
            urlInput.setText(store.getBaseUrl());
        }
        // The saved token is never shown; a blank field keeps it.
        if (!store.getToken().isEmpty()) {
            tokenLayout.setHint(getString(R.string.token_saved_hint));
        }

        testButton.setOnClickListener(v -> testConnection());
        saveButton.setOnClickListener(v -> save());
    }

    @Override
    public void onResume() {
        super.onResume();
        setTitle(R.string.title_settings);
    }

    /** Normalized URL from the field, or null after flagging the field. */
    private String readUrl() {
        urlLayout.setError(null);
        try {
            return BaseUrl.normalize(String.valueOf(urlInput.getText()));
        } catch (IllegalArgumentException e) {
            urlLayout.setError(e.getMessage());
            return null;
        }
    }

    /** Typed token, else the saved one; null after flagging the field if neither exists. */
    private String readToken() {
        tokenLayout.setError(null);
        String typed = String.valueOf(tokenInput.getText()).trim();
        if (!typed.isEmpty()) {
            return typed;
        }
        String saved = app().settings().getToken();
        if (saved.isEmpty()) {
            tokenLayout.setError(getString(R.string.error_token_required));
            return null;
        }
        return saved;
    }

    private void testConnection() {
        String url = readUrl();
        String token = readToken();
        if (url == null || token == null) {
            return;
        }
        setBusy(true);
        result.setText("");
        ApiClient client = new ApiClient(url, token, app().http());
        async(() -> ConnectionCheck.run(client), new com.lifeos.android.util.Async.Callback<ConnectionCheck.Outcome>() {
            @Override
            public void onSuccess(ConnectionCheck.Outcome outcome) {
                setBusy(false);
                showOutcome(outcome);
            }

            @Override
            public void onError(Throwable error) {
                setBusy(false);
                showError(error);
            }
        });
    }

    private void showOutcome(ConnectionCheck.Outcome outcome) {
        @StringRes int message;
        switch (outcome.getResult()) {
            case OK:
                message = R.string.test_ok;
                break;
            case UNREACHABLE:
                message = R.string.test_unreachable;
                break;
            case BAD_TOKEN:
                message = R.string.test_bad_token;
                break;
            case FORBIDDEN_HOST:
                message = R.string.test_forbidden_host;
                break;
            case ERROR:
            default:
                message = R.string.test_error;
                break;
        }
        String text = getString(message);
        if (outcome.getDetail() != null
                && (outcome.getResult() == ConnectionCheck.Result.ERROR
                        || outcome.getResult() == ConnectionCheck.Result.UNREACHABLE)) {
            text += "\n" + outcome.getDetail();
        }
        result.setText(text);
    }

    private void save() {
        String url = readUrl();
        String token = readToken();
        if (url == null || token == null) {
            return;
        }
        try {
            app().settings().save(url, token);
        } catch (GeneralSecurityException e) {
            Snackbars.info(requireView(), getString(R.string.error_save_failed, e.getMessage()));
            return;
        }
        app().settingsChanged();
        tokenInput.setText("");
        boolean wasRoot = getParentFragmentManager().getBackStackEntryCount() == 0;
        if (wasRoot) {
            navigator().showProjects();
        } else {
            navigator().back();
        }
    }

    private void setBusy(boolean busy) {
        progress.setVisibility(busy ? View.VISIBLE : View.GONE);
        testButton.setEnabled(!busy);
        saveButton.setEnabled(!busy);
    }
}
