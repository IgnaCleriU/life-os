package lifeos.adapters.rest;

import static org.hamcrest.Matchers.contains;
import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.nullValue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;

/** Endpoints REST de Task: mismo contrato que el adapter FastAPI. */
class TaskEndpointsTest extends RestTestSupport {

    private org.springframework.test.web.servlet.ResultActions patchJson(String url, String json) throws Exception {
        return mvc.perform(patch(url).contentType(MediaType.APPLICATION_JSON).content(json));
    }

    private org.springframework.test.web.servlet.ResultActions postBody(String url, String json) throws Exception {
        return mvc.perform(post(url).contentType(MediaType.APPLICATION_JSON).content(json));
    }

    @Test
    void createTaskUnderExistingProjectReturns201() throws Exception {
        String project = createProject("Project");

        postBody("/projects/" + project + "/tasks", "{\"title\": \"Do something\"}")
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.project_id").value(project))
                .andExpect(jsonPath("$.status").value("todo"))
                .andExpect(jsonPath("$.priority").value("medium"))
                .andExpect(jsonPath("$.due_date").value(nullValue()));
    }

    @Test
    void responseHasExactlyThePythonFields() throws Exception {
        String project = createProject("Project");

        postBody("/projects/" + project + "/tasks",
                        "{\"title\": \"T\", \"priority\": \"high\", \"due_date\": \"2026-01-01\", \"description\": \"d\"}")
                .andExpect(jsonPath("$.*", hasSize(8)))
                .andExpect(jsonPath("$.deleted_at").doesNotExist())
                .andExpect(jsonPath("$.title").value("T"))
                .andExpect(jsonPath("$.description").value("d"))
                .andExpect(jsonPath("$.priority").value("high"))
                .andExpect(jsonPath("$.due_date").value("2026-01-01"))
                .andExpect(jsonPath("$.created_at").exists());
    }

    @Test
    void createTaskUnderMissingProjectReturns404() throws Exception {
        postBody("/projects/" + UUID.randomUUID() + "/tasks", "{\"title\": \"Do something\"}")
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error.code").value("project_not_found"));
    }

    @Test
    void createTaskWithBlankTitleReturns400() throws Exception {
        String project = createProject("Project");

        postBody("/projects/" + project + "/tasks", "{\"title\": \"  \"}")
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error.code").value("domain_validation_error"));
    }

    @Test
    void createTaskMissingTitleReturns422() throws Exception {
        String project = createProject("Project");

        postBody("/projects/" + project + "/tasks", "{}")
                .andExpect(status().isUnprocessableContent())
                .andExpect(jsonPath("$.error.code").value("request_validation_error"));
    }

    @Test
    void createTaskWithUnknownPriorityReturns422() throws Exception {
        String project = createProject("Project");

        postBody("/projects/" + project + "/tasks", "{\"title\": \"T\", \"priority\": \"urgent\"}")
                .andExpect(status().isUnprocessableContent())
                .andExpect(jsonPath("$.error.code").value("request_validation_error"));
    }

    @Test
    void createTaskWithInvalidDueDateReturns422() throws Exception {
        String project = createProject("Project");

        postBody("/projects/" + project + "/tasks", "{\"title\": \"T\", \"due_date\": \"mañana\"}")
                .andExpect(status().isUnprocessableContent())
                .andExpect(jsonPath("$.error.code").value("request_validation_error"));
    }

    @Test
    void listTasksReturnsOnlyThatProjectsTasks() throws Exception {
        String projectA = createProject("A");
        String projectB = createProject("B");
        String taskA = createTask(projectA, "{\"title\": \"Task A\"}");
        createTask(projectB, "{\"title\": \"Task B\"}");

        mvc.perform(get("/projects/" + projectA + "/tasks"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[*].id", contains(taskA)));
    }

    @Test
    void listTasksOfProjectAppliesStatusFilter() throws Exception {
        // Regresión: esta ruta ignoraba en silencio `status`/`due_before`/`q`.
        String project = createProject("Project");
        String todo = createTask(project, "{\"title\": \"Pendiente\"}");
        String done = createTask(project, "{\"title\": \"Hecha\"}");
        mvc.perform(post("/tasks/" + done + "/complete"));

        mvc.perform(get("/projects/" + project + "/tasks?status=todo"))
                .andExpect(jsonPath("$[*].id", contains(todo)));
    }

    @Test
    void listTasksUnknownProjectReturnsEmptyList() throws Exception {
        mvc.perform(get("/projects/" + UUID.randomUUID() + "/tasks"))
                .andExpect(status().isOk())
                .andExpect(content().json("[]"));
    }

    @Test
    void updateTaskPartialFields() throws Exception {
        String task = createTask(createProject("Project"), "{\"title\": \"Original\"}");

        patchJson("/tasks/" + task, "{\"title\": \"Renamed\"}")
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.title").value("Renamed"))
                .andExpect(jsonPath("$.due_date").value(nullValue()));
    }

    @Test
    void updateTaskDueDateOmittedLeavesUnchanged() throws Exception {
        String task = createTask(createProject("Project"), "{\"title\": \"Task\", \"due_date\": \"2026-01-01\"}");

        patchJson("/tasks/" + task, "{\"title\": \"Task renamed\"}")
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.due_date").value("2026-01-01"));
    }

    @Test
    void updateTaskDueDateExplicitNullClearsIt() throws Exception {
        String task = createTask(createProject("Project"), "{\"title\": \"Task\", \"due_date\": \"2026-01-01\"}");

        patchJson("/tasks/" + task, "{\"due_date\": null}")
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.due_date").value(nullValue()));
    }

    @Test
    void updateTaskPriorityAndExplicitNullTitleIsANoOp() throws Exception {
        String task = createTask(createProject("Project"), "{\"title\": \"Task\"}");

        patchJson("/tasks/" + task, "{\"title\": null, \"priority\": \"low\"}")
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.title").value("Task"))
                .andExpect(jsonPath("$.priority").value("low"));
    }

    @Test
    void updateTaskWithUnknownPriorityReturns422() throws Exception {
        String task = createTask(createProject("Project"), "{\"title\": \"Task\"}");

        patchJson("/tasks/" + task, "{\"priority\": \"urgent\"}")
                .andExpect(status().isUnprocessableContent())
                .andExpect(jsonPath("$.error.code").value("request_validation_error"));
    }

    @Test
    void updateMissingTaskReturns404() throws Exception {
        patchJson("/tasks/" + UUID.randomUUID(), "{\"title\": \"New\"}")
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error.code").value("task_not_found"));
    }

    @Test
    void completeTaskReturnsDoneStatus() throws Exception {
        String task = createTask(createProject("Project"), "{\"title\": \"Task\"}");

        mvc.perform(post("/tasks/" + task + "/complete"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("done"));
    }

    @Test
    void completeTaskIsIdempotent() throws Exception {
        String task = createTask(createProject("Project"), "{\"title\": \"Task\"}");

        mvc.perform(post("/tasks/" + task + "/complete")).andExpect(status().isOk());
        mvc.perform(post("/tasks/" + task + "/complete"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("done"));
    }

    @Test
    void completeMissingTaskReturns404() throws Exception {
        mvc.perform(post("/tasks/" + UUID.randomUUID() + "/complete"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error.code").value("task_not_found"));
    }

    @Test
    void getTaskReturnsIt() throws Exception {
        String task = createTask(createProject("Project"), "{\"title\": \"Task\"}");

        mvc.perform(get("/tasks/" + task)).andExpect(status().isOk()).andExpect(jsonPath("$.id").value(task));
    }

    @Test
    void getMissingTaskReturns404() throws Exception {
        mvc.perform(get("/tasks/" + UUID.randomUUID()))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error.code").value("task_not_found"));
    }

    @Test
    void updateTaskDescriptionExplicitNullClearsIt() throws Exception {
        String task = createTask(createProject("Project"), "{\"title\": \"Task\", \"description\": \"original\"}");

        patchJson("/tasks/" + task, "{\"description\": null}")
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.description").value(nullValue()));
    }

    @Test
    void startAndReopenTask() throws Exception {
        String task = createTask(createProject("Project"), "{\"title\": \"Task\"}");

        mvc.perform(post("/tasks/" + task + "/start")).andExpect(jsonPath("$.status").value("doing"));
        mvc.perform(post("/tasks/" + task + "/reopen")).andExpect(jsonPath("$.status").value("todo"));
    }

    @Test
    void moveTaskToAnotherProject() throws Exception {
        String origin = createProject("Origin");
        String destination = createProject("Destination");
        String task = createTask(origin, "{\"title\": \"Task\"}");

        postBody("/tasks/" + task + "/move", "{\"project_id\": \"" + destination + "\"}")
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.project_id").value(destination));
    }

    @Test
    void moveTaskToMissingProjectReturns404() throws Exception {
        String task = createTask(createProject("Project"), "{\"title\": \"Task\"}");

        postBody("/tasks/" + task + "/move", "{\"project_id\": \"" + UUID.randomUUID() + "\"}")
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error.code").value("project_not_found"));
    }

    @Test
    void moveTaskWithoutProjectIdReturns422() throws Exception {
        String task = createTask(createProject("Project"), "{\"title\": \"Task\"}");

        postBody("/tasks/" + task + "/move", "{}")
                .andExpect(status().isUnprocessableContent())
                .andExpect(jsonPath("$.error.code").value("request_validation_error"));
    }

    @Test
    void deleteAndRestoreTask() throws Exception {
        String task = createTask(createProject("Project"), "{\"title\": \"Task\"}");

        mvc.perform(delete("/tasks/" + task)).andExpect(status().isNoContent()).andExpect(content().string(""));
        mvc.perform(get("/tasks/" + task)).andExpect(status().isNotFound());

        mvc.perform(post("/tasks/" + task + "/restore")).andExpect(status().isOk());
        mvc.perform(get("/tasks/" + task)).andExpect(status().isOk());
    }

    @Test
    void listTasksAcrossProjectsWithFilters() throws Exception {
        String projectA = createProject("A");
        String projectB = createProject("B");
        String taskA = createTask(projectA, "{\"title\": \"Pagar expensas\", \"due_date\": \"2026-07-01\"}");
        createTask(projectB, "{\"title\": \"Otra cosa\", \"due_date\": \"2026-12-01\"}");

        mvc.perform(get("/tasks?due_before=2026-07-28")).andExpect(jsonPath("$[*].id", contains(taskA)));
        mvc.perform(get("/tasks?q=EXPENSAS")).andExpect(jsonPath("$[*].id", contains(taskA)));
        mvc.perform(get("/tasks?project_id=" + projectB))
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].title").value("Otra cosa"));
    }

    @Test
    void listTasksWithInvalidFiltersReturns422() throws Exception {
        mvc.perform(get("/tasks?status=pending")).andExpect(status().isUnprocessableContent());
        mvc.perform(get("/tasks?due_before=ayer")).andExpect(status().isUnprocessableContent());
        mvc.perform(get("/tasks?project_id=nope"))
                .andExpect(status().isUnprocessableContent())
                .andExpect(jsonPath("$.error.code").value("request_validation_error"));
    }

    @Test
    void restoreTaskUnderDeletedProjectReturns404() throws Exception {
        // Regresión: borrar la única tarea deja el proyecto vacío y borrable;
        // restaurar la tarea después no debe reflotarla colgada de un proyecto invisible.
        String project = createProject("Project");
        String task = createTask(project, "{\"title\": \"Task\"}");
        mvc.perform(delete("/tasks/" + task));
        mvc.perform(delete("/projects/" + project)).andExpect(status().isNoContent());

        mvc.perform(post("/tasks/" + task + "/restore"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error.code").value("project_not_found"));
        mvc.perform(get("/tasks/" + task)).andExpect(status().isNotFound());
    }
}
