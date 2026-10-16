package com.lifeos.android.ui;

import static org.junit.Assert.fail;
import static org.robolectric.Shadows.shadowOf;

import android.os.Looper;
import java.util.function.BooleanSupplier;

/** Waiting helper: API calls run on background threads and reply through the main looper. */
final class UiTestSupport {

    private UiTestSupport() {}

    /** Runs the main looper until {@code condition} holds, failing after a few seconds. */
    static void waitFor(String what, BooleanSupplier condition) {
        long deadline = System.currentTimeMillis() + 10_000;
        while (System.currentTimeMillis() < deadline) {
            shadowOf(Looper.getMainLooper()).idle();
            if (condition.getAsBoolean()) {
                return;
            }
            try {
                Thread.sleep(20);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                fail("Interrupted while waiting for " + what);
            }
        }
        fail("Timed out waiting for " + what);
    }
}
