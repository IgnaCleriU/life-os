package com.lifeos.android.api.model;

/**
 * Any failed call to the Life OS API. Carries the HTTP status (0 when no
 * response was received), the machine-readable {@code error.code} and the
 * server's message. Use {@link #getKind()} (or the {@code is*} helpers) to
 * decide how to react.
 */
public class ApiException extends Exception {

    /** Broad failure categories the UI treats differently. */
    public enum Kind {
        /** No HTTP response: DNS, TLS, timeout, connection refused, offline. */
        NETWORK,
        /** 401: missing or wrong bearer token. */
        UNAUTHORIZED,
        /** 403 with code {@code forbidden_host}: the host is not in LIFEOS_ALLOWED_HOSTS. */
        FORBIDDEN_HOST,
        /** Any other 403. */
        FORBIDDEN,
        /** 404 (project_not_found, task_not_found, or an unknown route). */
        NOT_FOUND,
        /** 409 (e.g. project_not_empty: deleting a project that still has tasks). */
        CONFLICT,
        /** 400 or 422: the server rejected the input. */
        VALIDATION,
        /** 5xx. */
        SERVER,
        /** The app has no URL/token yet (nothing was sent). */
        NOT_CONFIGURED,
        /** 2xx with a body that is not the expected JSON, or any other status. */
        OTHER
    }

    public static final String CODE_FORBIDDEN_HOST = "forbidden_host";
    public static final String CODE_PROJECT_NOT_EMPTY = "project_not_empty";

    private final Kind kind;
    private final int status;
    private final String code;

    public ApiException(Kind kind, int status, String code, String message, Throwable cause) {
        super(message, cause);
        this.kind = kind;
        this.status = status;
        this.code = code;
    }

    /** A failure without an HTTP response. */
    public static ApiException network(Throwable cause) {
        String detail = cause.getMessage() == null ? cause.getClass().getSimpleName() : cause.getMessage();
        return new ApiException(Kind.NETWORK, 0, "network_error", detail, cause);
    }

    /** Thrown before any request when Settings are empty. */
    public static ApiException notConfigured() {
        return new ApiException(Kind.NOT_CONFIGURED, 0, "not_configured", "API URL and token are not set.", null);
    }

    /** Builds the exception for an error response, classifying it by status and code. */
    public static ApiException fromResponse(int status, String code, String message) {
        return new ApiException(kindFor(status, code), status, code, message, null);
    }

    static Kind kindFor(int status, String code) {
        if (status == 401) {
            return Kind.UNAUTHORIZED;
        }
        if (status == 403) {
            return CODE_FORBIDDEN_HOST.equals(code) ? Kind.FORBIDDEN_HOST : Kind.FORBIDDEN;
        }
        if (status == 404) {
            return Kind.NOT_FOUND;
        }
        if (status == 409) {
            return Kind.CONFLICT;
        }
        if (status == 400 || status == 422) {
            return Kind.VALIDATION;
        }
        if (status >= 500) {
            return Kind.SERVER;
        }
        return Kind.OTHER;
    }

    public Kind getKind() {
        return kind;
    }

    /** HTTP status, or 0 if there was no response. */
    public int getStatus() {
        return status;
    }

    /** The server's {@code error.code}, or a synthetic one ({@code network_error}, {@code http_502}...). */
    public String getCode() {
        return code;
    }

    public boolean isNetwork() {
        return kind == Kind.NETWORK;
    }

    public boolean isUnauthorized() {
        return kind == Kind.UNAUTHORIZED;
    }

    public boolean isForbiddenHost() {
        return kind == Kind.FORBIDDEN_HOST;
    }

    public boolean isNotFound() {
        return kind == Kind.NOT_FOUND;
    }

    /** True for the 409 raised when deleting a project that still has live tasks. */
    public boolean isProjectNotEmpty() {
        return kind == Kind.CONFLICT && CODE_PROJECT_NOT_EMPTY.equals(code);
    }
}
