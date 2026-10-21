package com.lifeos.android;

import com.lifeos.android.api.ApiClient;
import com.lifeos.android.api.model.ApiException;

/**
 * Application for the UI smoke tests: every screen talks to {@link #baseUrl}, normally a
 * MockWebServer, instead of the saved settings (no Keystore, no real server).
 */
public final class TestApp extends LifeOsApp {

    /** Set by the test before launching a screen. */
    public static volatile String baseUrl = "http://localhost:1/";

    @Override
    public synchronized ApiClient api() throws ApiException {
        return new ApiClient(baseUrl, "test-token", http());
    }
}
