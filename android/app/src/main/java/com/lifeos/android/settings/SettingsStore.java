package com.lifeos.android.settings;

import android.content.Context;
import android.content.SharedPreferences;
import java.security.GeneralSecurityException;

/**
 * Where the app keeps the API base URL (plain) and the bearer token
 * (AES/GCM-encrypted with an Android Keystore key). Backups are disabled in
 * the manifest: a restored ciphertext could not be decrypted on another device.
 */
public final class SettingsStore {

    private static final String PREFS = "lifeos_settings";
    private static final String KEY_BASE_URL = "base_url";
    private static final String KEY_TOKEN = "token_encrypted";

    private final SharedPreferences prefs;
    private final TokenCipher cipher = new TokenCipher();

    public SettingsStore(Context context) {
        this.prefs = context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    /** The normalized base URL, or an empty string when not set. */
    public String getBaseUrl() {
        return prefs.getString(KEY_BASE_URL, "");
    }

    /** The decrypted token, or an empty string when not set or no longer decryptable. */
    public String getToken() {
        String stored = prefs.getString(KEY_TOKEN, null);
        if (stored == null) {
            return "";
        }
        try {
            return cipher.decrypt(stored);
        } catch (GeneralSecurityException | IllegalArgumentException e) {
            // Key lost (e.g. new lock screen policy, restored backup): the user must re-enter it.
            return "";
        }
    }

    /** True when both a URL and a token are available. */
    public boolean isConfigured() {
        return !getBaseUrl().isEmpty() && !getToken().isEmpty();
    }

    /**
     * Saves the settings. {@code baseUrl} is normalized by {@link BaseUrl#normalize}.
     *
     * @throws IllegalArgumentException if the URL is unusable
     * @throws GeneralSecurityException if the token could not be encrypted
     */
    public void save(String baseUrl, String token) throws GeneralSecurityException {
        String normalized = BaseUrl.normalize(baseUrl);
        String encrypted = cipher.encrypt(token.trim());
        prefs.edit().putString(KEY_BASE_URL, normalized).putString(KEY_TOKEN, encrypted).apply();
    }
}
