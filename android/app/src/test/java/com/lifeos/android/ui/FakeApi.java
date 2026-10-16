package com.lifeos.android.ui;

import java.io.IOException;
import okhttp3.mockwebserver.Dispatcher;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;

/** A tiny fake of the Life OS REST API for the UI smoke tests: one project with three tasks. */
final class FakeApi {

    static final String PROJECT_ID = "11111111-1111-1111-1111-111111111111";
    static final String PROJECT_NAME = "Home";

    private static final String PROJECT = "{\"id\":\"" + PROJECT_ID + "\",\"name\":\"" + PROJECT_NAME
            + "\",\"description\":null,\"status\":\"active\",\"created_at\":\"2026-10-16T12:30:45Z\"}";

    private static String task(String id, String title, String status, String priority) {
        return "{\"id\":\"" + id + "\",\"project_id\":\"" + PROJECT_ID + "\",\"title\":\"" + title
                + "\",\"description\":\"Details\",\"status\":\"" + status + "\",\"priority\":\"" + priority
                + "\",\"due_date\":\"2020-01-01\",\"created_at\":\"2026-10-16T12:30:45Z\"}";
    }

    private static final String TASKS = "[" + task("t1", "Fix tap", "todo", "high") + ","
            + task("t2", "Buy paint", "todo", "low") + ","
            + task("t3", "Call plumber", "doing", "medium") + ","
            + task("t4", "Sweep", "done", "low") + "]";

    private final MockWebServer server = new MockWebServer();

    FakeApi() throws IOException {
        server.setDispatcher(new Dispatcher() {
            @Override
            public MockResponse dispatch(RecordedRequest request) {
                String path = request.getPath() == null ? "" : request.getPath();
                String body;
                if (path.startsWith("/projects/" + PROJECT_ID + "/tasks")) {
                    body = TASKS;
                } else if (path.startsWith("/projects/" + PROJECT_ID)) {
                    body = PROJECT;
                } else if (path.startsWith("/projects")) {
                    body = "[" + PROJECT + "]";
                } else {
                    return new MockResponse().setResponseCode(404).setBody("{\"detail\":\"not found\"}");
                }
                return new MockResponse().setHeader("Content-Type", "application/json").setBody(body);
            }
        });
        server.start();
    }

    String baseUrl() {
        return server.url("/").toString();
    }

    void shutdown() throws IOException {
        server.shutdown();
    }
}
