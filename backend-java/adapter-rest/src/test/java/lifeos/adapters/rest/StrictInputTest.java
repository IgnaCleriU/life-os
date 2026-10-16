package lifeos.adapters.rest;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.ResultActions;

/** Entradas que Pydantic rechaza con 422 y Java no puede aceptar en silencio. */
class StrictInputTest extends RestTestSupport {

    private ResultActions postBody(String url, String json) throws Exception {
        return mvc.perform(post(url).contentType(MediaType.APPLICATION_JSON).content(json));
    }

    private static void is422(ResultActions result) throws Exception {
        result.andExpect(status().isUnprocessableContent())
                .andExpect(jsonPath("$.error.code").value("request_validation_error"));
    }

    @Test
    void nonCanonicalUuidInPathIsRejected() throws Exception {
        // UUID.fromString acepta "1-1-1-1-1": sin esto sería un 404.
        is422(mvc.perform(get("/projects/1-1-1-1-1")));
        is422(mvc.perform(get("/tasks/1-1-1-1-1")));
    }

    @Test
    void nonCanonicalUuidInQueryAndBodyIsRejected() throws Exception {
        String task = createTask(createProject("P"), "{\"title\": \"T\"}");

        is422(mvc.perform(get("/tasks?project_id=1-1-1-1-1")));
        is422(postBody("/tasks/" + task + "/move", "{\"project_id\": \"1-1-1-1-1\"}"));
    }

    @Test
    void numbersAreNotCoercedToStrings() throws Exception {
        String project = createProject("P");

        is422(postBody("/projects", "{\"name\": 5}"));
        is422(postBody("/projects", "{\"name\": \"x\", \"description\": 5}"));
        is422(postBody("/projects/" + project + "/tasks", "{\"title\": 5}"));
        is422(postBody("/projects/" + project + "/tasks", "{\"title\": \"T\", \"priority\": 1}"));
        String task = createTask(project, "{\"title\": \"T\"}");
        is422(postBody("/tasks/" + task + "/move", "{\"project_id\": 5}"));
    }

    @Test
    void nonObjectBodyIsRejected() throws Exception {
        is422(postBody("/projects", "[\"Life OS\"]"));
        is422(mvc.perform(patch("/projects/" + createProject("P"))
                .contentType(MediaType.APPLICATION_JSON).content("\"x\"")));
    }

    @Test
    void commaSeparatedStatusIsRejected() throws Exception {
        // Spring separa por comas al bindear List<String>; FastAPI no, y responde 422.
        is422(mvc.perform(get("/projects?status=active,archived")));
        is422(mvc.perform(get("/tasks?status=todo,doing")));
        is422(mvc.perform(get("/projects/" + createProject("P") + "/tasks?status=todo,doing")));
    }

    @Test
    void emptyStatusFilterIsRejected() throws Exception {
        is422(mvc.perform(get("/projects?status=")));
        is422(mvc.perform(get("/tasks?status=")));
    }
}
