package com.lifeos.android.util;

import android.os.Handler;
import android.os.Looper;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Minimal background-work helper: run a blocking call on a small thread pool
 * and get the result back on the main thread. A cancelled {@link Call} never
 * reaches its callback, so cancel in {@code onDestroyView} to avoid touching
 * a dead view ({@code BaseFragment.async} does this for you).
 */
public final class Async {

    private static final ExecutorService EXECUTOR = Executors.newFixedThreadPool(4);
    private static final Handler MAIN = new Handler(Looper.getMainLooper());

    private Async() {}

    /** Receives the outcome on the main thread. */
    public interface Callback<T> {
        void onSuccess(T result);

        /** {@code error} is an {@code ApiException} for API failures. */
        void onError(Throwable error);
    }

    /** Handle to an in-flight call. */
    public static final class Call {
        private volatile boolean cancelled;

        /** After this the callback is never invoked (the work itself is not interrupted). */
        public void cancel() {
            cancelled = true;
        }

        public boolean isCancelled() {
            return cancelled;
        }
    }

    public static <T> Call run(Callable<T> work, Callback<T> callback) {
        Call call = new Call();
        EXECUTOR.execute(() -> {
            T result = null;
            Throwable failure = null;
            try {
                result = work.call();
            } catch (Throwable t) {
                failure = t;
            }
            T finalResult = result;
            Throwable finalFailure = failure;
            MAIN.post(() -> {
                if (call.isCancelled()) {
                    return;
                }
                if (finalFailure != null) {
                    callback.onError(finalFailure);
                } else {
                    callback.onSuccess(finalResult);
                }
            });
        });
        return call;
    }

    /** For work with no result (delete, ...). */
    public interface VoidWork {
        void run() throws Exception;
    }

    public static Call runVoid(VoidWork work, Callback<Void> callback) {
        return run(() -> {
            work.run();
            return null;
        }, callback);
    }
}
