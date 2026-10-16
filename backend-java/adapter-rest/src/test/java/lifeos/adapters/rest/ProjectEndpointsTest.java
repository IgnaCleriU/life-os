package lifeos.adapters.rest;

import static org.hamcrest.Matchers.contains;
import static org.hamcrest.Matchers.containsInAnyOrder;
import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.matchesPattern;
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

/** Endpoints REST de Project: mismo contrato que el adapter FastAPI. */
class ProjectEndpointsTest extends RestTestSupport {

    @Test
    void createProjectReturns201AndBody() throws Exception {
        mvc.perform(post("/projects").contentType(MediaType.APPLICATION_JSON).content("{\"name\": \"Life OS\"}"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.name").value("Life OS"))
                .andExpect(jsonPath("$.description").value(nullValue()))
                .andExpect(jsonPath("$.status").value("active"))
                .andExpect(jsonPath("$.id").exists())
                .andExpect(jsonPath("$.created_at").exists());
    }

    @Test
    void responseHasExactlyThePythonFields() throws Exception {
        // `deleted_at` no se expone; los nombres van en snake_case; las fechas en
        // ISO-8601 UTC con "Z", como las serializa Pydantic.
        mvc.perform(post("/projects").contentType(MediaType.APPLICATION_JSON).content("{\"name\": \"Life OS\"}"))
                .andExpect(jsonPath("$.*", hasSize(5)))
                .andExpect(jsonPath("$.deleted_at").doesNotExist())
                .andExpect(jsonPath("$.created_at")
                        .value(matchesPattern("\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{6})?Z")));
    }

    @Test
    void createProjectWithBlankNameReturns400() throws Exception {
        mvc.perform(post("/projects").contentType(MediaType.APPLICATION_JSON).content("{\"name\": \"   \"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error.code").value("domain_validation_error"))
                .andExpect(jsonPath("$.error.message").value("El nombre del proyecto no puede estar vacío"));
    }

    @Test
    void createProjectMissingNameReturns422() throws Exception {
        mvc.perform(post("/projects").contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isUnprocessableContent())
                .andExpect(jsonPath("$.error.code").value("request_validation_error"));
    }

    @Test
    void createProjectWithMalformedJsonReturns422() throws Exception {
        mvc.perform(post("/projects").contentType(MediaType.APPLICATION_JSON).content("{\"name\": "))
                .andExpect(status().isUnprocessableContent())
                .andExpect(jsonPath("$.error.code").value("request_validation_error"))
                // Mensaje estable: sin detalles internos del parser de Jackson.
                .andExpect(jsonPath("$.error.message").value("El body no es JSON válido"));
    }

    @Test
    void listProjectsReturnsCreatedProjects() throws Exception {
        String first = createProject("First");
        String second = createProject("Second");

        mvc.perform(get("/projects"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[*].id", containsInAnyOrder(first, second)));
    }

    @Test
    void listProjectsEmptyReturnsEmptyList() throws Exception {
        mvc.perform(get("/projects")).andExpect(status().isOk()).andExpect(content().json("[]"));
    }

    @Test
    void getProjectReturnsIt() throws Exception {
        String id = createProject("Life OS");

        mvc.perform(get("/projects/" + id)).andExpect(status().isOk()).andExpect(jsonPath("$.id").value(id));
    }

    @Test
    void getMissingProjectReturns404() throws Exception {
        mvc.perform(get("/projects/" + UUID.randomUUID()))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error.code").value("project_not_found"));
    }

    @Test
    void getProjectWithInvalidUuidReturns422() throws Exception {
        mvc.perform(get("/projects/no-es-un-uuid"))
                .andExpect(status().isUnprocessableContent())
                .andExpect(jsonPath("$.error.code").value("request_validation_error"));
    }

    @Test
    void updateProjectPartialFields() throws Exception {
        String id = createProject("Original");

        mvc.perform(patch("/projects/" + id).contentType(MediaType.APPLICATION_JSON).content("{\"name\": \"Renamed\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("Renamed"));
    }

    @Test
    void updateProjectDescriptionOmittedLeavesUnchanged() throws Exception {
        String id = idOf(postJson("/projects", "{\"name\": \"Life OS\", \"description\": \"original\"}"));

        mvc.perform(patch("/projects/" + id).contentType(MediaType.APPLICATION_JSON).content("{\"name\": \"Life OS v2\"}"))
                .andExpect(jsonPath("$.description").value("original"));
    }

    @Test
    void updateProjectDescriptionExplicitNullClearsIt() throws Exception {
        String id = idOf(postJson("/projects", "{\"name\": \"Life OS\", \"description\": \"original\"}"));

        mvc.perform(patch("/projects/" + id).contentType(MediaType.APPLICATION_JSON).content("{\"description\": null}"))
                .andExpect(jsonPath("$.description").value(nullValue()));
    }

    @Test
    void updateProjectWithExplicitNullNameIsANoOp() throws Exception {
        String id = createProject("Life OS");

        mvc.perform(patch("/projects/" + id).contentType(MediaType.APPLICATION_JSON).content("{\"name\": null}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("Life OS"));
    }

    @Test
    void completeArchiveActivateProject() throws Exception {
        String id = createProject("Life OS");

        mvc.perform(post("/projects/" + id + "/complete")).andExpect(jsonPath("$.status").value("completed"));
        mvc.perform(post("/projects/" + id + "/archive")).andExpect(jsonPath("$.status").value("archived"));
        mvc.perform(post("/projects/" + id + "/activate")).andExpect(jsonPath("$.status").value("active"));
    }

    @Test
    void listProjectsFiltersByStatus() throws Exception {
        createProject("Active");
        String archived = createProject("Archived");
        mvc.perform(post("/projects/" + archived + "/archive"));

        mvc.perform(get("/projects?status=archived")).andExpect(jsonPath("$[*].id", contains(archived)));
    }

    @Test
    void listProjectsAcceptsRepeatedStatus() throws Exception {
        String active = createProject("Active");
        String archived = createProject("Archived");
        mvc.perform(post("/projects/" + archived + "/archive"));
        String completed = createProject("Completed");
        mvc.perform(post("/projects/" + completed + "/complete"));

        mvc.perform(get("/projects?status=active&status=archived"))
                .andExpect(jsonPath("$[*].id", contains(active, archived)));
    }

    @Test
    void listProjectsWithUnknownStatusReturns422() throws Exception {
        mvc.perform(get("/projects?status=nope"))
                .andExpect(status().isUnprocessableContent())
                .andExpect(jsonPath("$.error.code").value("request_validation_error"));
    }

    @Test
    void listProjectsFiltersByText() throws Exception {
        String casa = createProject("Casa de campo");
        createProject("Finanzas");

        mvc.perform(get("/projects?q=CASA")).andExpect(jsonPath("$[*].id", contains(casa)));
    }

    @Test
    void deleteEmptyProjectReturns204AndHidesIt() throws Exception {
        String id = createProject("Vacio");

        mvc.perform(delete("/projects/" + id))
                .andExpect(status().isNoContent())
                .andExpect(content().string(""));
        mvc.perform(get("/projects/" + id)).andExpect(status().isNotFound());
    }

    @Test
    void deleteProjectWithLiveTasksReturns409() throws Exception {
        String id = createProject("Con tareas");
        createTask(id, "{\"title\": \"Tarea\"}");

        mvc.perform(delete("/projects/" + id))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.error.code").value("project_not_empty"));
    }

    @Test
    void restoreProjectMakesItVisibleAgain() throws Exception {
        String id = createProject("Vacio");
        mvc.perform(delete("/projects/" + id));

        mvc.perform(post("/projects/" + id + "/restore")).andExpect(status().isOk());
        mvc.perform(get("/projects/" + id)).andExpect(status().isOk());
    }
}
