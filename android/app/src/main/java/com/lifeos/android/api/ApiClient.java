package com.lifeos.android.api;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParseException;
import com.google.gson.JsonParser;
import com.lifeos.android.api.model.ApiException;
import com.lifeos.android.api.model.Priority;
import com.lifeos.android.api.model.Project;
import com.lifeos.android.api.model.ProjectPatch;
import com.lifeos.android.api.model.ProjectStatus;
import com.lifeos.android.api.model.Task;
import com.lifeos.android.api.model.TaskPatch;
import com.lifeos.android.api.model.TaskQuery;
import com.lifeos.android.api.model.TaskStatus;
import java.io.IOException;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.TimeUnit;
import okhttp3.HttpUrl;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import okhttp3.ResponseBody;

/**
 * Blocking client for the Life OS REST API (same contract as the Python and
 * Java backends). Every method may throw {@link ApiException}; none of them
 * may be called on the main thread. From the UI go through
 * {@link com.lifeos.android.util.Async}.
 *
 * <p>Instances are cheap and thread-safe; they are immutable, so after the
 * settings change get a fresh one from {@code LifeOsApp.api()}.
 */
public final class ApiClient {

    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");

    private final HttpUrl baseUrl;
    private final String token;
    private final OkHttpClient http;

    /**
     * @param baseUrl normalized API root, e.g. {@code https://host.ts.net} (see
     *     {@link com.lifeos.android.settings.BaseUrl})
     * @param token bearer token sent on every call except {@link #health()}
     */
    public ApiClient(String baseUrl, String token, OkHttpClient http) {
        HttpUrl parsed = HttpUrl.parse(baseUrl);
        if (parsed == null) {
            throw new IllegalArgumentException("Invalid base URL: " + baseUrl);
        }
        this.baseUrl = parsed;
        this.token = token == null ? "" : token.trim();
        this.http = http;
    }

    /** An OkHttp client with timeouts suited to a phone on a VPN. Share one per process. */
    public static OkHttpClient defaultHttpClient() {
        return new OkHttpClient.Builder()
                .connectTimeout(10, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .callTimeout(45, TimeUnit.SECONDS)
                .build();
    }

    // ---------------------------------------------------------------- health

    /** {@code GET /health}: the only unauthenticated route. Succeeds if the server answers 2xx. */
    public void health() throws ApiException {
        execute(new Request.Builder().url(url("health").build()).get(), false, null);
    }

    // -------------------------------------------------------------- projects

    /** {@code GET /projects}. Empty/null {@code statuses} = every status; null {@code text} = no search. */
    public List<Project> listProjects(List<ProjectStatus> statuses, String text) throws ApiException {
        HttpUrl.Builder url = url("projects");
        if (statuses != null) {
            for (ProjectStatus status : statuses) {
                url.addQueryParameter("status", status.value());
            }
        }
        addIfPresent(url, "q", text);
        return asList(execute(get(url), true, Project[].class));
    }

    public Project getProject(String id) throws ApiException {
        return execute(get(url("projects", id)), true, Project.class);
    }

    /** {@code POST /projects}. {@code description} may be null. */
    public Project createProject(String name, String description) throws ApiException {
        JsonObject body = new JsonObject();
        body.addProperty("name", name);
        if (description != null) {
            body.addProperty("description", description);
        }
        return execute(post(url("projects"), body), true, Project.class);
    }

    /** {@code PATCH /projects/{id}}: sends only what the patch sets. */
    public Project updateProject(String id, ProjectPatch patch) throws ApiException {
        return execute(patch(url("projects", id), patch.toJson()), true, Project.class);
    }

    public Project completeProject(String id) throws ApiException {
        return execute(post(url("projects", id, "complete"), null), true, Project.class);
    }

    public Project archiveProject(String id) throws ApiException {
        return execute(post(url("projects", id, "archive"), null), true, Project.class);
    }

    public Project activateProject(String id) throws ApiException {
        return execute(post(url("projects", id, "activate"), null), true, Project.class);
    }

    /** Undoes a delete. There is no way to list deleted projects, so use it right after {@link #deleteProject}. */
    public Project restoreProject(String id) throws ApiException {
        return execute(post(url("projects", id, "restore"), null), true, Project.class);
    }

    /**
     * Soft-deletes a project. Fails with a 409 ({@link ApiException#isProjectNotEmpty()}) while it
     * still has live tasks: surface that to the user, do not retry.
     */
    public void deleteProject(String id) throws ApiException {
        execute(new Request.Builder().url(url("projects", id).build()).delete(), true, null);
    }

    // ----------------------------------------------------------------- tasks

    /** {@code GET /projects/{id}/tasks}. {@code query.getProjectId()} is ignored. */
    public List<Task> listProjectTasks(String projectId, TaskQuery query) throws ApiException {
        HttpUrl.Builder url = url("projects", projectId, "tasks");
        addTaskFilters(url, query);
        return asList(execute(get(url), true, Task[].class));
    }

    /** {@code GET /tasks}, across projects; {@code query.getProjectId()} narrows to one project. */
    public List<Task> listTasks(TaskQuery query) throws ApiException {
        HttpUrl.Builder url = url("tasks");
        addIfPresent(url, "project_id", query.getProjectId());
        addTaskFilters(url, query);
        return asList(execute(get(url), true, Task[].class));
    }

    public Task getTask(String id) throws ApiException {
        return execute(get(url("tasks", id)), true, Task.class);
    }

    /**
     * {@code POST /projects/{id}/tasks}. {@code priority}, {@code dueDate} and {@code description} may
     * be null (the server defaults the priority to medium).
     */
    public Task createTask(String projectId, String title, Priority priority, LocalDate dueDate, String description)
            throws ApiException {
        JsonObject body = new JsonObject();
        body.addProperty("title", title);
        if (priority != null) {
            body.addProperty("priority", priority.value());
        }
        if (dueDate != null) {
            body.addProperty("due_date", dueDate.toString());
        }
        if (description != null) {
            body.addProperty("description", description);
        }
        return execute(post(url("projects", projectId, "tasks"), body), true, Task.class);
    }

    /** {@code PATCH /tasks/{id}}: sends only what the patch sets. */
    public Task updateTask(String id, TaskPatch patch) throws ApiException {
        return execute(patch(url("tasks", id), patch.toJson()), true, Task.class);
    }

    /** Moves the task to the "doing" column. */
    public Task startTask(String id) throws ApiException {
        return execute(post(url("tasks", id, "start"), null), true, Task.class);
    }

    /** Moves the task to the "done" column. */
    public Task completeTask(String id) throws ApiException {
        return execute(post(url("tasks", id, "complete"), null), true, Task.class);
    }

    /** Moves the task back to the "todo" column. */
    public Task reopenTask(String id) throws ApiException {
        return execute(post(url("tasks", id, "reopen"), null), true, Task.class);
    }

    /** Undoes a delete. There is no way to list deleted tasks, so use it right after {@link #deleteTask}. */
    public Task restoreTask(String id) throws ApiException {
        return execute(post(url("tasks", id, "restore"), null), true, Task.class);
    }

    /** Moves a task to another project. */
    public Task moveTask(String id, String targetProjectId) throws ApiException {
        JsonObject body = new JsonObject();
        body.addProperty("project_id", targetProjectId);
        return execute(post(url("tasks", id, "move"), body), true, Task.class);
    }

    public void deleteTask(String id) throws ApiException {
        execute(new Request.Builder().url(url("tasks", id).build()).delete(), true, null);
    }

    // --------------------------------------------------------------- plumbing

    private static void addTaskFilters(HttpUrl.Builder url, TaskQuery query) {
        for (TaskStatus status : query.getStatuses()) {
            url.addQueryParameter("status", status.value());
        }
        addIfPresent(url, "q", query.getText());
        if (query.getDueBefore() != null) {
            url.addQueryParameter("due_before", query.getDueBefore().toString());
        }
    }

    private static void addIfPresent(HttpUrl.Builder url, String name, String value) {
        if (value != null && !value.isEmpty()) {
            url.addQueryParameter(name, value);
        }
    }

    private HttpUrl.Builder url(String... segments) {
        HttpUrl.Builder builder = baseUrl.newBuilder();
        for (String segment : segments) {
            builder.addPathSegment(segment);
        }
        return builder;
    }

    private static Request.Builder get(HttpUrl.Builder url) {
        return new Request.Builder().url(url.build()).get();
    }

    private static Request.Builder post(HttpUrl.Builder url, JsonObject body) {
        return new Request.Builder().url(url.build()).post(jsonBody(body));
    }

    private static Request.Builder patch(HttpUrl.Builder url, JsonObject body) {
        return new Request.Builder().url(url.build()).patch(jsonBody(body));
    }

    /** Action endpoints take no body; they get an empty JSON object so the request is well-formed. */
    private static RequestBody jsonBody(JsonObject body) {
        // JsonElement.toString() keeps explicit nulls; Gson.toJson(JsonElement) would drop them.
        return RequestBody.create((body == null ? new JsonObject() : body).toString(), JSON);
    }

    private static <T> List<T> asList(T[] array) {
        return Arrays.asList(array);
    }

    /** Runs the request and returns the parsed body, or null when {@code type} is null (204 / ignored body). */
    private <T> T execute(Request.Builder request, boolean authenticated, Class<T> type) throws ApiException {
        request.header("Accept", "application/json");
        if (authenticated) {
            request.header("Authorization", "Bearer " + token);
        }
        try (Response response = http.newCall(request.build()).execute()) {
            ResponseBody body = response.body();
            if (!response.isSuccessful()) {
                throw errorFrom(response.code(), body == null ? "" : body.string());
            }
            if (type == null) {
                return null;
            }
            String text = body == null ? "" : body.string();
            try {
                T parsed = ApiJson.GSON.fromJson(text, type);
                if (parsed == null) {
                    throw new JsonParseException("Empty response body");
                }
                return parsed;
            } catch (JsonParseException e) {
                throw new ApiException(
                        ApiException.Kind.OTHER, response.code(), "bad_response",
                        "The server sent a response this app cannot read.", e);
            }
        } catch (IOException e) {
            throw ApiException.network(e);
        } catch (IllegalArgumentException e) {
            // OkHttp rejects header values with control characters (e.g. a pasted newline in the token).
            throw new ApiException(
                    ApiException.Kind.OTHER, 0, "invalid_request", "Invalid request: " + e.getMessage(), e);
        }
    }

    private static ApiException errorFrom(int status, String text) {
        try {
            JsonElement root = JsonParser.parseString(text);
            if (root.isJsonObject() && root.getAsJsonObject().get("error") != null
                    && root.getAsJsonObject().get("error").isJsonObject()) {
                JsonObject error = root.getAsJsonObject().getAsJsonObject("error");
                String code = stringOrNull(error, "code");
                String message = stringOrNull(error, "message");
                return ApiException.fromResponse(
                        status,
                        code == null ? "http_" + status : code,
                        message == null || message.isEmpty() ? "HTTP " + status : message);
            }
        } catch (JsonParseException ignored) {
            // Not JSON (e.g. an HTML page from a proxy): fall through to the generic error.
        }
        return ApiException.fromResponse(status, "http_" + status, "Unexpected response (HTTP " + status + ")");
    }

    private static String stringOrNull(JsonObject object, String name) {
        JsonElement element = object.get(name);
        return element == null || element.isJsonNull() || !element.isJsonPrimitive() ? null : element.getAsString();
    }
}
