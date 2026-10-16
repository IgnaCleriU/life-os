package lifeos.adapters.rest;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.hamcrest.Matchers.allOf;
import static org.hamcrest.Matchers.containsString;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.Optional;
import java.util.UUID;
import lifeos.application.port.ProjectRepository;
import lifeos.application.usecase.GetProject;
import lifeos.domain.Project;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.test.context.bean.override.mockito.MockitoSpyBean;

/**
 * Todo error sale con la forma {@code {"error": {"code", "message"}}}: los
 * clientes leen {@code error.code} y el 500 o 404 por defecto de Spring los
 * rompería.
 */
class ErrorShapesTest extends RestTestSupport {

    @MockitoSpyBean
    GetProject getProject;

    @MockitoSpyBean
    ProjectRepository projectRepository;

    @Test
    void unknownRouteReturns404WithErrorShape() throws Exception {
        mvc.perform(get("/no-existe"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error.code").value("not_found"));
    }

    @Test
    void unsupportedMethodReturns405WithErrorShape() throws Exception {
        mvc.perform(put("/projects"))
                .andExpect(status().isMethodNotAllowed())
                .andExpect(jsonPath("$.error.code").value("method_not_allowed"))
                .andExpect(header().string("Allow", allOf(containsString("GET"), containsString("POST"))));
    }

    @Test
    void notAcceptableKeepsItsStatus() throws Exception {
        // Antes caía en el handler genérico y salía como 500.
        mvc.perform(get("/projects").accept(MediaType.APPLICATION_XML))
                .andExpect(status().isNotAcceptable());
    }

    @Test
    void springStatusExceptionsKeepTheirStatusAndTheErrorShape() throws Exception {
        UUID id = UUID.randomUUID();
        Mockito.doThrow(new ResponseStatusException(HttpStatus.I_AM_A_TEAPOT)).when(getProject).execute(id);

        mvc.perform(get("/projects/" + id))
                .andExpect(status().isIAmATeapot())
                .andExpect(jsonPath("$.error.code").value("i_am_a_teapot"));
    }

    @Test
    void realForeignKeyViolationReturns409() throws Exception {
        // Un proyecto que el repositorio "ve" pero que no está en la base: el
        // INSERT de la tarea dispara la FK real de SQLite, no un mock.
        Project ghost = Project.create("Fantasma", null);
        Mockito.doReturn(Optional.of(ghost)).when(projectRepository).get(ghost.id(), false);

        mvc.perform(post("/projects/" + ghost.id() + "/tasks")
                        .contentType(MediaType.APPLICATION_JSON).content("{\"title\": \"T\"}"))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.error.code").value("integrity_error"));
    }

    @Test
    void nonJsonContentTypeReturns422() throws Exception {
        mvc.perform(post("/projects").contentType(MediaType.TEXT_PLAIN).content("name=x"))
                .andExpect(status().isUnprocessableContent())
                .andExpect(jsonPath("$.error.code").value("request_validation_error"));
    }

    @Test
    void integrityViolationReturns409WithErrorShape() throws Exception {
        UUID id = UUID.randomUUID();
        Mockito.doThrow(new DataIntegrityViolationException("FOREIGN KEY constraint failed"))
                .when(getProject).execute(id);

        mvc.perform(get("/projects/" + id))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.error.code").value("integrity_error"));
    }

    @Test
    void unexpectedFailureReturns500WithErrorShape() throws Exception {
        UUID id = UUID.randomUUID();
        Mockito.doThrow(new IllegalStateException("boom")).when(getProject).execute(id);

        mvc.perform(get("/projects/" + id))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.error.code").value("internal_error"));
    }
}
