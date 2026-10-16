package com.lifeos.android.settings;

import java.util.Locale;
import okhttp3.HttpUrl;

/** Turns whatever the user typed into the canonical API root the client uses. */
public final class BaseUrl {

    private BaseUrl() {}

    /**
     * Trims, adds {@code https://} when no scheme was typed, drops trailing
     * slashes, and keeps an optional path prefix. Only http and https are
     * accepted (plain http is still blocked at runtime by the network security
     * config outside debug builds).
     *
     * @throws IllegalArgumentException with a user-readable message when the input is unusable
     */
    public static String normalize(String input) {
        String text = input == null ? "" : input.trim();
        if (text.isEmpty()) {
            throw new IllegalArgumentException("Enter the API URL.");
        }
        String lower = text.toLowerCase(Locale.ROOT);
        if (!lower.startsWith("http://") && !lower.startsWith("https://")) {
            if (text.contains("://")) {
                throw new IllegalArgumentException("Only http:// and https:// URLs are supported.");
            }
            text = "https://" + text;
        }
        HttpUrl url = HttpUrl.parse(text);
        if (url == null) {
            throw new IllegalArgumentException("That is not a valid URL.");
        }
        if (url.query() != null || url.fragment() != null) {
            throw new IllegalArgumentException("Remove the query string or fragment from the URL.");
        }
        String result = url.toString();
        while (result.endsWith("/")) {
            result = result.substring(0, result.length() - 1);
        }
        return result;
    }
}
