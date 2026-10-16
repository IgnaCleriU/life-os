package com.lifeos.android;

import android.app.Application;
import android.content.Context;
import com.lifeos.android.api.ApiClient;
import com.lifeos.android.api.model.ApiException;
import com.lifeos.android.settings.SettingsStore;
import okhttp3.OkHttpClient;

/** Process-wide singletons: the settings store, the shared HTTP client and the current {@link ApiClient}. */
public class LifeOsApp extends Application {

    private SettingsStore settings;
    private OkHttpClient http;
    private ApiClient api;

    @Override
    public void onCreate() {
        super.onCreate();
        settings = new SettingsStore(this);
        http = ApiClient.defaultHttpClient();
    }

    public static LifeOsApp from(Context context) {
        return (LifeOsApp) context.getApplicationContext();
    }

    public SettingsStore settings() {
        return settings;
    }

    /** The shared OkHttp client (connection pool); use it to build ad-hoc {@link ApiClient}s. */
    public OkHttpClient http() {
        return http;
    }

    /**
     * The client for the saved settings. Reads the Keystore on first use, so call it from a
     * background thread (inside the {@code Callable} given to {@code Async.run}).
     *
     * @throws ApiException of kind NOT_CONFIGURED when URL or token are missing
     */
    public synchronized ApiClient api() throws ApiException {
        if (api == null) {
            String baseUrl = settings.getBaseUrl();
            String token = settings.getToken();
            if (baseUrl.isEmpty() || token.isEmpty()) {
                throw ApiException.notConfigured();
            }
            api = new ApiClient(baseUrl, token, http);
        }
        return api;
    }

    /** Drops the cached client; call after saving new settings. */
    public synchronized void settingsChanged() {
        api = null;
    }
}
