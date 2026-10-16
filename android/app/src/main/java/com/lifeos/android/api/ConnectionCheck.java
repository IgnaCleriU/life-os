package com.lifeos.android.api;

import com.lifeos.android.api.model.ApiException;

/**
 * The "Test connection" probe: {@code GET /health} (is anything there?) then
 * {@code GET /projects} (does the token work and is this host allowed?).
 * Blocking; run it off the main thread.
 */
public final class ConnectionCheck {

    public enum Result {
        OK,
        /** No HTTP response at all (DNS, TLS, timeout, Tailscale down...). */
        UNREACHABLE,
        /** The server answered 401 on an authenticated route. */
        BAD_TOKEN,
        /** 403 forbidden_host: the host name must be added to LIFEOS_ALLOWED_HOSTS on the server. */
        FORBIDDEN_HOST,
        /** Anything else; {@link Outcome#getDetail()} has the server's message. */
        ERROR
    }

    public static final class Outcome {
        private final Result result;
        private final String detail;

        Outcome(Result result, String detail) {
            this.result = result;
            this.detail = detail;
        }

        public Result getResult() {
            return result;
        }

        /** The underlying error message, or null for {@link Result#OK}. */
        public String getDetail() {
            return detail;
        }
    }

    private ConnectionCheck() {}

    public static Outcome run(ApiClient client) {
        try {
            client.health();
            client.listProjects(null, null);
            return new Outcome(Result.OK, null);
        } catch (ApiException e) {
            switch (e.getKind()) {
                case NETWORK:
                    return new Outcome(Result.UNREACHABLE, e.getMessage());
                case UNAUTHORIZED:
                    return new Outcome(Result.BAD_TOKEN, e.getMessage());
                case FORBIDDEN_HOST:
                    return new Outcome(Result.FORBIDDEN_HOST, e.getMessage());
                default:
                    return new Outcome(Result.ERROR, e.getMessage());
            }
        }
    }
}
