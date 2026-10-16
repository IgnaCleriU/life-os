package com.lifeos.android.ui;

import android.os.Bundle;
import android.view.View;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.annotation.StringRes;
import androidx.fragment.app.Fragment;
import com.lifeos.android.LifeOsApp;
import com.lifeos.android.api.ApiClient;
import com.lifeos.android.api.model.ApiException;
import com.lifeos.android.util.Async;
import com.lifeos.android.util.ErrorMessages;
import com.lifeos.android.util.Snackbars;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Callable;

/**
 * Base class for the screens. Gives them the API, navigation, a title helper
 * and {@link #async}, which cancels pending calls when the view goes away so a
 * late response never touches a destroyed view.
 */
public abstract class BaseFragment extends Fragment {

    private final List<Async.Call> pending = new ArrayList<>();

    protected BaseFragment() {}

    protected BaseFragment(int layoutId) {
        super(layoutId);
    }

    protected LifeOsApp app() {
        return LifeOsApp.from(requireContext());
    }

    protected Navigator navigator() {
        return Navigator.from(this);
    }

    /**
     * The configured client. Blocking on first use (Keystore read), so only call it inside the
     * work given to {@link #async}: {@code async(() -> api().listProjects(null, null), cb)}.
     */
    protected ApiClient api() throws ApiException {
        return app().api();
    }

    /** Sets the top app bar title. Call from {@code onResume}. */
    protected void setTitle(@StringRes int title) {
        requireActivity().setTitle(title);
    }

    protected void setTitle(CharSequence title) {
        requireActivity().setTitle(title);
    }

    /** Runs {@code work} off the main thread; the callback runs on the main thread unless the view is gone. */
    protected <T> Async.Call async(Callable<T> work, Async.Callback<T> callback) {
        Async.Call call = Async.run(work, callback);
        pending.add(call);
        return call;
    }

    /** Same as {@link #async} for work without a result. */
    protected Async.Call asyncVoid(Async.VoidWork work, Async.Callback<Void> callback) {
        Async.Call call = Async.runVoid(work, callback);
        pending.add(call);
        return call;
    }

    /** Shows the error as a Snackbar, with a Settings action when the fix is there. */
    protected void showError(Throwable error) {
        View root = getView();
        if (root == null) {
            return;
        }
        if (ErrorMessages.needsSettings(error)) {
            Snackbars.errorWithSettings(root, error, () -> navigator().openSettings());
        } else {
            Snackbars.error(root, error);
        }
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        pending.clear();
    }

    @Override
    public void onDestroyView() {
        for (Async.Call call : pending) {
            call.cancel();
        }
        pending.clear();
        super.onDestroyView();
    }
}
