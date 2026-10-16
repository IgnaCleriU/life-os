package com.lifeos.android.api;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import com.google.gson.JsonObject;
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
import java.time.Instant;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import okhttp3.mockwebserver.SocketPolicy;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

public class ApiClientTest {

    private static final String PROJECT_JSON = "{\"id\":\"11111111-1111-1111-1111-111111111111\","
            + "\"name\":\"Home\",\"description\":null,\"status\":\"active\","
            + "\"created_at\":\"2026-10-16T12:30:45.123456Z\"}";
    private static final String TASK_JSON = "{\"id\":\"22222222-2222-2222-2222-222222222222\","
            + "\"project_id\":\"11111111-1111-1111-1111-111111111111\",\"title\":\"Fix tap\","
            + "\"description\":\"Kitchen\",\"status\":\"doing\",\"priority\":\"high\","
            + "\"due_date\":\"2026-11-01\",\"created_at\":\"2026-10-16T12:30:45Z\"}";

    private MockWebServer server;
    private ApiClient client;

    @Before
    public void setUp() throws IOException {
        server = new MockWebServer();
        server.start();
        client = new ApiClient(server.url("/").toString(), "secret-token", ApiClient.defaultHttpClient());
    }

    @After
    public void tearDown() throws IOException {
        server.shutdown();
    }

    private static MockResponse json(int code, String body) {
        return new MockResponse().setResponseCode(code).setHeader("Content-Type", "application/json").setBody(body);
    }

    private RecordedRequest take() throws InterruptedException {
        return server.takeRequest();
    }

    private static JsonObject bodyOf(RecordedRequest request) {
        return JsonParser.parseString(request.getBody().readUtf8()).getAsJsonObject();
    }

    private ApiException failure(ThrowingRun run) {
        try {
            run.run();
        } catch (ApiException e) {
            return e;
        }
        fail("Expected ApiException");
        return null;
    }

    private interface ThrowingRun {
        void run() throws ApiException;
    }

    // ------------------------------------------------------------------ auth

    @Test
    public void sendsBearerTokenOnAuthenticatedCalls() throws Exception {
        server.enqueue(json(200, "[]"));
        client.listProjects(null, null);
        RecordedRequest request = take();
        assertEquals("Bearer secret-token", request.getHeader("Authorization"));
        assertEquals("/projects", request.getPath());
    }

    @Test
    public void healthDoesNotSendTheToken() throws Exception {
        server.enqueue(json(200, "{\"status\":\"ok\"}"));
        client.health();
        RecordedRequest request = take();
        assertEquals("/health", request.getPath());
        assertNull(request.getHeader("Authorization"));
    }

    // --------------------------------------------------------------- parsing

    @Test
    public void parsesProject() throws Exception {
        server.enqueue(json(200, "[" + PROJECT_JSON + "]"));
        List<Project> projects = client.listProjects(null, null);
        assertEquals(1, projects.size());
        Project p = projects.get(0);
        assertEquals("11111111-1111-1111-1111-111111111111", p.getId());
        assertEquals("Home", p.getName());
        assertNull(p.getDescription());
        assertEquals(ProjectStatus.ACTIVE, p.getStatus());
        assertEquals(Instant.parse("2026-10-16T12:30:45.123456Z"), p.getCreatedAt());
    }

    @Test
    public void parsesTask() throws Exception {
        server.enqueue(json(200, TASK_JSON));
        Task t = client.getTask("22222222-2222-2222-2222-222222222222");
        assertEquals("/tasks/22222222-2222-2222-2222-222222222222", take().getPath());
        assertEquals("11111111-1111-1111-1111-111111111111", t.getProjectId());
        assertEquals("Fix tap", t.getTitle());
        assertEquals("Kitchen", t.getDescription());
        assertEquals(TaskStatus.DOING, t.getStatus());
        assertEquals(Priority.HIGH, t.getPriority());
        assertEquals(LocalDate.of(2026, 11, 1), t.getDueDate());
        assertEquals(Instant.parse("2026-10-16T12:30:45Z"), t.getCreatedAt());
    }

    @Test
    public void taskWithNullDueDateAndUnknownEnumValue() throws Exception {
        server.enqueue(json(200, TASK_JSON.replace("\"2026-11-01\"", "null").replace("\"doing\"", "\"blocked\"")));
        Task t = client.getTask("x");
        assertNull(t.getDueDate());
        assertNull(t.getStatus());
    }

    // ---------------------------------------------------------- list filters

    @Test
    public void projectListEncodesRepeatedStatusAndText() throws Exception {
        server.enqueue(json(200, "[]"));
        client.listProjects(Arrays.asList(ProjectStatus.ACTIVE, ProjectStatus.COMPLETED), "a&b c");
        assertEquals("/projects?status=active&status=completed&q=a%26b%20c", take().getPath());
    }

    @Test
    public void taskListEncodesFilters() throws Exception {
        server.enqueue(json(200, "[]"));
        client.listTasks(TaskQuery.builder()
                .status(TaskStatus.TODO)
                .status(TaskStatus.DOING)
                .text("buy milk")
                .dueBefore(LocalDate.of(2026, 12, 31))
                .projectId("p1")
                .build());
        assertEquals(
                "/tasks?project_id=p1&status=todo&status=doing&q=buy%20milk&due_before=2026-12-31",
                take().getPath());
    }

    @Test
    public void projectTaskListUsesPathAndIgnoresQueryProjectId() throws Exception {
        server.enqueue(json(200, "[" + TASK_JSON + "]"));
        List<Task> tasks = client.listProjectTasks("p1", TaskQuery.builder().projectId("other").status(TaskStatus.DONE).build());
        assertEquals(1, tasks.size());
        assertEquals("/projects/p1/tasks?status=done", take().getPath());
    }

    @Test
    public void noFiltersMeansNoQueryString() throws Exception {
        server.enqueue(json(200, "[]"));
        client.listTasks(TaskQuery.all());
        assertEquals("/tasks", take().getPath());
    }

    // ------------------------------------------------------------ write calls

    @Test
    public void createProjectSendsOnlyGivenFields() throws Exception {
        server.enqueue(json(201, PROJECT_JSON));
        client.createProject("Home", null);
        RecordedRequest request = take();
        assertEquals("POST", request.getMethod());
        JsonObject body = bodyOf(request);
        assertEquals("Home", body.get("name").getAsString());
        assertFalse(body.has("description"));
    }

    @Test
    public void createTaskBody() throws Exception {
        server.enqueue(json(201, TASK_JSON));
        client.createTask("p1", "Fix tap", Priority.LOW, LocalDate.of(2026, 11, 1), null);
        RecordedRequest request = take();
        assertEquals("/projects/p1/tasks", request.getPath());
        JsonObject body = bodyOf(request);
        assertEquals("Fix tap", body.get("title").getAsString());
        assertEquals("low", body.get("priority").getAsString());
        assertEquals("2026-11-01", body.get("due_date").getAsString());
        assertFalse(body.has("description"));
    }

    @Test
    public void projectPatchOnlyContainsChangedFields() throws Exception {
        server.enqueue(json(200, PROJECT_JSON));
        client.updateProject("p1", new ProjectPatch().name("New"));
        RecordedRequest request = take();
        assertEquals("PATCH", request.getMethod());
        JsonObject body = bodyOf(request);
        assertEquals(1, body.size());
        assertEquals("New", body.get("name").getAsString());
    }

    @Test
    public void projectPatchCanClearDescriptionWithExplicitNull() throws Exception {
        server.enqueue(json(200, PROJECT_JSON));
        client.updateProject("p1", new ProjectPatch().clearDescription());
        JsonObject body = bodyOf(take());
        assertEquals(1, body.size());
        assertTrue(body.has("description"));
        assertTrue(body.get("description").isJsonNull());
    }

    @Test
    public void taskPatchOnlyContainsChangedFields() throws Exception {
        server.enqueue(json(200, TASK_JSON));
        client.updateTask("t1", new TaskPatch().title("X").priority(Priority.MEDIUM));
        JsonObject body = bodyOf(take());
        assertEquals(2, body.size());
        assertEquals("X", body.get("title").getAsString());
        assertEquals("medium", body.get("priority").getAsString());
    }

    @Test
    public void taskPatchClearsDueDateAndDescriptionWithNulls() throws Exception {
        server.enqueue(json(200, TASK_JSON));
        client.updateTask("t1", new TaskPatch().clearDueDate().clearDescription());
        JsonObject body = bodyOf(take());
        assertEquals(2, body.size());
        assertTrue(body.get("due_date").isJsonNull());
        assertTrue(body.get("description").isJsonNull());
    }

    @Test
    public void taskPatchSetsDueDate() throws Exception {
        server.enqueue(json(200, TASK_JSON));
        client.updateTask("t1", new TaskPatch().dueDate(LocalDate.of(2027, 1, 2)));
        assertEquals("2027-01-02", bodyOf(take()).get("due_date").getAsString());
    }

    @Test
    public void actionEndpointsUsePostOnTheRightPaths() throws Exception {
        for (int i = 0; i < 4; i++) {
            server.enqueue(json(200, PROJECT_JSON));
        }
        client.completeProject("p");
        client.archiveProject("p");
        client.activateProject("p");
        client.restoreProject("p");
        server.enqueue(json(200, TASK_JSON));
        server.enqueue(json(200, TASK_JSON));
        server.enqueue(json(200, TASK_JSON));
        client.startTask("t");
        client.completeTask("t");
        client.reopenTask("t");
        String[] expected = {
            "/projects/p/complete", "/projects/p/archive", "/projects/p/activate", "/projects/p/restore",
            "/tasks/t/start", "/tasks/t/complete", "/tasks/t/reopen"
        };
        for (String path : expected) {
            RecordedRequest request = take();
            assertEquals("POST", request.getMethod());
            assertEquals(path, request.getPath());
        }
    }

    @Test
    public void restoreAndMoveTask() throws Exception {
        server.enqueue(json(200, TASK_JSON));
        server.enqueue(json(200, TASK_JSON));
        client.restoreTask("t");
        client.moveTask("t", "p2");
        assertEquals("/tasks/t/restore", take().getPath());
        RecordedRequest move = take();
        assertEquals("/tasks/t/move", move.getPath());
        assertEquals("p2", bodyOf(move).get("project_id").getAsString());
    }

    @Test
    public void deleteReturns204WithoutBody() throws Exception {
        server.enqueue(new MockResponse().setResponseCode(204));
        server.enqueue(new MockResponse().setResponseCode(204));
        client.deleteTask("t");
        client.deleteProject("p");
        RecordedRequest first = take();
        assertEquals("DELETE", first.getMethod());
        assertEquals("/tasks/t", first.getPath());
        assertEquals("/projects/p", take().getPath());
    }

    @Test
    public void baseUrlWithPathPrefixIsKept() throws Exception {
        ApiClient prefixed = new ApiClient(server.url("/api").toString(), "t", ApiClient.defaultHttpClient());
        server.enqueue(json(200, "[]"));
        prefixed.listProjects(null, null);
        assertEquals("/api/projects", take().getPath());
    }

    // ---------------------------------------------------------------- errors

    private static String error(String code, String message) {
        return "{\"error\":{\"code\":\"" + code + "\",\"message\":\"" + message + "\"}}";
    }

    @Test
    public void unauthorizedIsMapped() {
        server.enqueue(json(401, error("unauthorized", "Missing token")));
        ApiException e = failure(() -> client.listProjects(null, null));
        assertEquals(ApiException.Kind.UNAUTHORIZED, e.getKind());
        assertEquals(401, e.getStatus());
        assertEquals("unauthorized", e.getCode());
        assertEquals("Missing token", e.getMessage());
        assertTrue(e.isUnauthorized());
    }

    @Test
    public void forbiddenHostIsDistinguishedFromOtherForbidden() {
        server.enqueue(json(403, error("forbidden_host", "nope")));
        server.enqueue(json(403, error("forbidden", "nope")));
        ApiException host = failure(() -> client.listProjects(null, null));
        ApiException other = failure(() -> client.listProjects(null, null));
        assertEquals(ApiException.Kind.FORBIDDEN_HOST, host.getKind());
        assertTrue(host.isForbiddenHost());
        assertEquals(ApiException.Kind.FORBIDDEN, other.getKind());
    }

    @Test
    public void notFoundIsMapped() {
        server.enqueue(json(404, error("project_not_found", "Project x not found")));
        ApiException e = failure(() -> client.getProject("x"));
        assertEquals(ApiException.Kind.NOT_FOUND, e.getKind());
        assertEquals("project_not_found", e.getCode());
    }

    @Test
    public void projectNotEmptyConflictIsMapped() {
        server.enqueue(json(409, error("project_not_empty", "Project has tasks")));
        ApiException e = failure(() -> client.deleteProject("p"));
        assertEquals(ApiException.Kind.CONFLICT, e.getKind());
        assertTrue(e.isProjectNotEmpty());
        assertEquals("Project has tasks", e.getMessage());
    }

    @Test
    public void validationErrorIsMapped() {
        server.enqueue(json(422, error("request_validation_error", "bad date")));
        ApiException e = failure(() -> client.createTask("p", "t", null, null, null));
        assertEquals(ApiException.Kind.VALIDATION, e.getKind());
        assertEquals(422, e.getStatus());
        assertEquals("bad date", e.getMessage());
    }

    @Test
    public void serverErrorIsMapped() {
        server.enqueue(json(500, error("internal_error", "Error interno")));
        assertEquals(ApiException.Kind.SERVER, failure(() -> client.listProjects(null, null)).getKind());
    }

    @Test
    public void nonJsonErrorBodyGivesGenericException() {
        server.enqueue(new MockResponse().setResponseCode(502).setBody("<html>Bad gateway</html>"));
        ApiException e = failure(() -> client.listProjects(null, null));
        assertEquals(502, e.getStatus());
        assertEquals("http_502", e.getCode());
        assertEquals(ApiException.Kind.SERVER, e.getKind());
        assertTrue(e.getMessage().contains("502"));
    }

    @Test
    public void emptyErrorBodyGivesGenericException() {
        server.enqueue(new MockResponse().setResponseCode(401));
        ApiException e = failure(() -> client.listProjects(null, null));
        assertEquals(ApiException.Kind.UNAUTHORIZED, e.getKind());
        assertEquals("http_401", e.getCode());
    }

    @Test
    public void successWithGarbageBodyIsBadResponse() {
        server.enqueue(new MockResponse().setResponseCode(200).setBody("<html>captive portal</html>"));
        ApiException e = failure(() -> client.listProjects(null, null));
        assertEquals(ApiException.Kind.OTHER, e.getKind());
        assertEquals("bad_response", e.getCode());
    }

    @Test
    public void networkFailureIsMapped() {
        server.enqueue(new MockResponse().setSocketPolicy(SocketPolicy.DISCONNECT_AT_START));
        ApiException e = failure(() -> client.listProjects(null, null));
        assertEquals(ApiException.Kind.NETWORK, e.getKind());
        assertTrue(e.isNetwork());
        assertEquals(0, e.getStatus());
    }

    @Test
    public void unreachableHostIsNetworkFailure() throws Exception {
        String url = server.url("/").toString();
        server.shutdown();
        ApiClient dead = new ApiClient(url, "t", ApiClient.defaultHttpClient());
        assertTrue(failure(dead::health).isNetwork());
        server = new MockWebServer(); // so tearDown has something to shut down
    }

    // ------------------------------------------------------ connection check

    @Test
    public void connectionCheckOk() {
        server.enqueue(json(200, "{\"status\":\"ok\"}"));
        server.enqueue(json(200, "[]"));
        assertEquals(ConnectionCheck.Result.OK, ConnectionCheck.run(client).getResult());
    }

    @Test
    public void connectionCheckBadToken() {
        server.enqueue(json(200, "{}"));
        server.enqueue(json(401, error("unauthorized", "no")));
        assertEquals(ConnectionCheck.Result.BAD_TOKEN, ConnectionCheck.run(client).getResult());
    }

    @Test
    public void connectionCheckForbiddenHost() {
        server.enqueue(json(200, "{}"));
        server.enqueue(json(403, error("forbidden_host", "no")));
        assertEquals(ConnectionCheck.Result.FORBIDDEN_HOST, ConnectionCheck.run(client).getResult());
    }

    @Test
    public void connectionCheckUnreachable() {
        server.enqueue(new MockResponse().setSocketPolicy(SocketPolicy.DISCONNECT_AT_START));
        assertEquals(ConnectionCheck.Result.UNREACHABLE, ConnectionCheck.run(client).getResult());
    }

    @Test
    public void tokenWithControlCharactersFailsWithoutEchoingIt() throws Exception {
        ApiClient bad = new ApiClient(server.url("/").toString(), "abc\ndef", ApiClient.defaultHttpClient());
        try {
            bad.listProjects(null, null);
            fail("Expected ApiException");
        } catch (ApiException e) {
            assertEquals("invalid_token", e.getCode());
            assertFalse(e.getMessage().contains("abc"));
        }
        assertEquals(0, server.getRequestCount());
    }

    @Test
    public void defaultClientDoesNotReplayRequestsAfterAConnectionFailure() {
        assertFalse(ApiClient.defaultHttpClient().retryOnConnectionFailure());
    }
}
